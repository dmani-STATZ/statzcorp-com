import json
import logging
import urllib.parse

from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from .auth import get_current_account, login_supplier, logout_supplier
from .emails import mask_email, send_set_password_link
from .forms import (
    SERVICE_UNAVAILABLE_ERROR,
    RequestAccessForm,
    SetPasswordForm,
    SupplierLoginForm,
)
from .presenters import present_supplier
from .statzweb_client import (
    StatzWebAPIError,
    StatzWebHTTPError,
    StatzWebNotConfigured,
    StatzWebUnavailable,
    get_document_download_url,
    get_supplier,
    verify_supplier,
)
from .tokens import read_set_password_token

logger = logging.getLogger(__name__)

# Well-formed 5-character CAGE so STATZWeb identifier-format validation is not
# confused with auth/network failures. Non-existent by design.
CONNECTION_TEST_CAGE_CODE = 'ZZZZZ'

SUPPLIER_NOT_FOUND_ERROR = (
    "Your company record isn't currently active in STATZ's supplier system. "
    "Please contact us at info@statzcorp.com or 608-798-4500 for assistance."
)


class SupplierLoginRequiredMixin:
    """Gate for portal pages — checks the supplier_portal session, not request.user."""

    def dispatch(self, request, *args, **kwargs):
        account = get_current_account(request)
        if account is None:
            messages.info(request, "Please log in to view your supplier data.")
            return redirect('supplier_portal:login')
        request.supplier_account = account
        return super().dispatch(request, *args, **kwargs)


class SupplierLoginView(FormView):
    template_name = 'supplier_portal/login.html'
    form_class = SupplierLoginForm
    success_url = reverse_lazy('supplier_portal:dashboard')

    def dispatch(self, request, *args, **kwargs):
        if get_current_account(request) is not None:
            return redirect('supplier_portal:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        login_supplier(self.request, form.account)
        return super().form_valid(form)


class SupplierLogoutView(View):
    def post(self, request, *args, **kwargs):
        logout_supplier(request)
        messages.success(request, "You have been logged out.")
        return redirect('supplier_portal:login')


class SupplierDashboardView(SupplierLoginRequiredMixin, TemplateView):
    template_name = 'supplier_portal/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.request.supplier_account
        context['account'] = account
        try:
            raw_profile = get_supplier(account.cage_code)
            if raw_profile is None:
                context.update({
                    'state': 'not_found',
                    'notice': SUPPLIER_NOT_FOUND_ERROR,
                })
            elif not isinstance(raw_profile, dict):
                raise StatzWebUnavailable(
                    "STATZWeb supplier profile response was not an object."
                )
            else:
                context.update({
                    'state': 'ok',
                    'supplier': present_supplier(raw_profile),
                })
        except StatzWebNotConfigured:
            logger.exception(
                "STATZWeb is not configured while loading dashboard for CAGE %s",
                account.cage_code,
            )
            context.update({
                'state': 'unavailable',
                'notice': SERVICE_UNAVAILABLE_ERROR,
            })
        except StatzWebUnavailable:
            logger.exception(
                "STATZWeb is unavailable while loading dashboard for CAGE %s",
                account.cage_code,
            )
            context.update({
                'state': 'unavailable',
                'notice': SERVICE_UNAVAILABLE_ERROR,
            })
        return context


class SupplierDocumentDownloadView(SupplierLoginRequiredMixin, View):
    def get(self, request, document_id):
        cage_code = request.supplier_account.cage_code
        try:
            url = get_document_download_url(cage_code, document_id)
            if url is None:
                messages.error(request, "That document is no longer available.")
                return redirect('supplier_portal:dashboard')
            try:
                scheme = urllib.parse.urlparse(url).scheme.lower()
            except ValueError as exc:
                raise StatzWebUnavailable(
                    "STATZWeb returned a malformed document URL."
                ) from exc
            if scheme not in {'http', 'https'}:
                raise StatzWebUnavailable(
                    "STATZWeb returned an unsupported document URL scheme."
                )
            response = HttpResponseRedirect(url)
            response['Cache-Control'] = 'no-store'
            return response
        except StatzWebNotConfigured:
            logger.exception(
                "STATZWeb is not configured while downloading a document for CAGE %s",
                cage_code,
            )
        except StatzWebUnavailable:
            logger.exception(
                "STATZWeb is unavailable while downloading a document for CAGE %s",
                cage_code,
            )
        messages.error(request, SERVICE_UNAVAILABLE_ERROR)
        return redirect('supplier_portal:dashboard')


class RequestAccessView(FormView):
    """
    Self-service access / forgot-password, step 1: enter a CAGE code.
    On success, shows the masked on-file email for confirmation before
    anything is sent — STATZ staff is never in the password chain.
    """

    template_name = 'supplier_portal/request_access.html'
    form_class = RequestAccessForm

    def form_valid(self, form):
        return render(self.request, 'supplier_portal/request_access_confirm.html', {
            'cage_code': form.account.cage_code,
            'masked_email': mask_email(form.account.contact_email),
        })


class SendPasswordLinkView(View):
    """Step 2: user confirmed the masked email — send the set-password link."""

    def post(self, request, *args, **kwargs):
        form = RequestAccessForm(request.POST)
        if not form.is_valid():
            return render(request, 'supplier_portal/request_access.html', {'form': form})

        account = form.account
        context = {'masked_email': mask_email(account.contact_email)}

        if not account.can_request_reset():
            context['recently_sent'] = True
            return render(request, 'supplier_portal/request_access_sent.html', context)

        if send_set_password_link(request, account):
            account.register_reset_request()
            return render(request, 'supplier_portal/request_access_sent.html', context)

        messages.error(
            request,
            "We couldn't send the email just now. Please try again shortly, or "
            "contact us at info@statzcorp.com or 608-798-4500.",
        )
        return redirect('supplier_portal:request_access')


class SetPasswordView(FormView):
    """Landing page for the emailed link: choose a password, then log in."""

    template_name = 'supplier_portal/set_password.html'
    form_class = SetPasswordForm

    def dispatch(self, request, *args, **kwargs):
        self.account = read_set_password_token(kwargs['token'])
        if self.account is None:
            return render(request, 'supplier_portal/set_password_invalid.html', status=410)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cage_code'] = self.account.cage_code
        return context

    def form_valid(self, form):
        self.account.set_password(form.cleaned_data['password1'])
        self.account.save(update_fields=['password', 'updated_at'])
        self.account.reset_failed_attempts()
        messages.success(self.request, "Your password has been set. You can now log in.")
        return redirect('supplier_portal:login')


def _config_diagnostics(cage_code):
    """Booleans and lengths only — never secret values or prefixes."""
    base_url = settings.SUPPLIER_PORTAL_API_BASE_URL or ''
    api_key = settings.SUPPLIER_PORTAL_API_KEY or ''
    hmac_secret = settings.SUPPLIER_PORTAL_HMAC_SECRET or ''
    parsed = urllib.parse.urlparse(base_url)
    path_component = parsed.path or ''
    verify_path = f"/suppliers/{urllib.parse.quote(cage_code, safe='')}/verify/"
    request_url = (base_url.rstrip('/') + verify_path) if base_url else ''
    scheme_host = ''
    if parsed.scheme and parsed.netloc:
        scheme_host = f"{parsed.scheme}://{parsed.netloc}"
    return {
        'base_url_configured': bool(base_url),
        'base_url_scheme_host': scheme_host,
        'base_url_path': path_component,
        'base_url_has_expected_prefix': '/api/supplier-portal/' in path_component,
        'request_url': request_url,
        'api_key_present': bool(api_key),
        'api_key_length': len(api_key),
        'hmac_secret_present': bool(hmac_secret),
        'hmac_secret_length': len(hmac_secret),
    }


def _interpret_connection_result(
    *,
    http_status,
    diagnostics,
    error_code=None,
    content_type='',
):
    prefix_ok = diagnostics.get('base_url_has_expected_prefix')
    ct = (content_type or '').lower()
    is_json = 'application/json' in ct

    if http_status == 403 and not prefix_ok:
        return (
            "Base URL is missing the /api/supplier-portal/ prefix — the request is "
            "landing outside STATZWeb's middleware exemption. Fix the "
            "SUPPLIER_PORTAL_API_BASE_URL App Setting first."
        )
    if (
        http_status == 403
        and prefix_ok
        and error_code is None
        and not is_json
    ):
        return (
            "Non-JSON 403 — consistent with an Azure App Service Access Restriction "
            "or WAF rule blocking this App Service's outbound IP, not with an "
            "application-level rejection."
        )
    if http_status == 403 and error_code is not None:
        return (
            "Application-level 403 from STATZWeb — the request authenticated but "
            "was not permitted."
        )
    if http_status == 401:
        return (
            "Authentication rejected: API key, HMAC secret mismatch, or clock skew "
            ">5 minutes."
        )
    if http_status == 404:
        return (
            "Success. STATZWeb was reached, authenticated, and correctly reported "
            "no such supplier."
        )
    if http_status == 200:
        return (
            "Success, and unexpectedly the test CAGE code exists. Verify the "
            "placeholder."
        )
    if http_status is None:
        return "No HTTP status — configuration or network failure before a response."
    return f"Unexpected status HTTP {http_status}."


def run_api_connection_test(cage_code=CONNECTION_TEST_CAGE_CODE):
    """
    Shared probe used by ApiConnectionTestView and the statzweb_ping command.
    Returns a dict safe for templates / stdout (no secret values).
    """
    result = {
        'success': False,
        'found': False,
        'data': None,
        'error': None,
        'http_status': None,
        'content_type': None,
        'body_snippet': None,
        'error_code': None,
        'error_message': None,
        'diagnostics': _config_diagnostics(cage_code),
        'interpretation': None,
        'cage_code': cage_code,
    }
    try:
        data = verify_supplier(cage_code)
        result['success'] = True
        result['found'] = data is not None
        result['data'] = data
        result['http_status'] = 200 if data is not None else 404
        result['interpretation'] = _interpret_connection_result(
            http_status=result['http_status'],
            diagnostics=result['diagnostics'],
        )
    except StatzWebHTTPError as exc:
        result['error'] = str(exc)
        result['http_status'] = exc.status
        result['content_type'] = exc.content_type
        result['body_snippet'] = exc.body_snippet
        result['error_code'] = exc.error_code
        result['error_message'] = exc.error_message
        if exc.request_url:
            result['diagnostics']['request_url'] = exc.request_url
        result['interpretation'] = _interpret_connection_result(
            http_status=exc.status,
            diagnostics=result['diagnostics'],
            error_code=exc.error_code,
            content_type=exc.content_type,
        )
    except StatzWebNotConfigured as exc:
        result['error'] = str(exc)
        result['interpretation'] = _interpret_connection_result(
            http_status=None,
            diagnostics=result['diagnostics'],
        )
    except StatzWebAPIError as exc:
        result['error'] = str(exc)
        result['interpretation'] = _interpret_connection_result(
            http_status=None,
            diagnostics=result['diagnostics'],
        )
    except json.JSONDecodeError as exc:
        result['error'] = f"Response was not valid JSON: {exc}"
        result['interpretation'] = (
            "STATZWeb (or an intermediary) returned a non-JSON body where JSON "
            "was expected."
        )
    return result


class ApiConnectionTestView(UserPassesTestMixin, TemplateView):
    """
    TEMPORARY diagnostic page — verifies statzcorp-com can reach STATZWeb's
    Supplier Portal API (network path + signed auth), independent of any
    real supplier data. Uses a well-formed but non-existent CAGE code —
    a clean "not found" response is just as much proof of success as a
    "found" one, since either means the request reached STATZWeb and was
    authenticated correctly. Only a StatzWebAPIError means the pipe itself
    is broken.

    Staff-only. Remove this view, its URL, its template, and the login-page
    link once the production path is confirmed working end to end.
    """

    template_name = 'supplier_portal/api_test.html'
    raise_exception = True

    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(run_api_connection_test(CONNECTION_TEST_CAGE_CODE))
        return context
