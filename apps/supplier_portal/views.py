from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView

from .auth import get_current_account, login_supplier, logout_supplier
from .emails import mask_email, send_set_password_link
from .forms import RequestAccessForm, SetPasswordForm, SupplierLoginForm
from .statzweb_client import StatzWebAPIError, StatzWebNotConfigured, verify_supplier
from .tokens import read_set_password_token


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
        context['account'] = self.request.supplier_account
        return context


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


class ApiConnectionTestView(TemplateView):
    """
    TEMPORARY diagnostic page — verifies statzcorp-com can reach STATZWeb's
    Supplier Portal API (network path + signed auth), independent of any
    real supplier data. Uses a placeholder CAGE code that's expected NOT to
    exist — a clean "not found" response is just as much proof of success
    as a "found" one, since either means the request reached STATZWeb and
    was authenticated correctly. Only a StatzWebAPIError means the pipe
    itself is broken.

    Remove this view, its URL, its template, and the login-page link once
    the production VNet integration is confirmed working end to end.
    """

    template_name = 'supplier_portal/api_test.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            data = verify_supplier('CONNECTION-TEST-PLACEHOLDER')
            context['success'] = True
            context['found'] = data is not None
            context['data'] = data
        except StatzWebNotConfigured as exc:
            context['success'] = False
            context['error'] = str(exc)
        except StatzWebAPIError as exc:
            context['success'] = False
            context['error'] = str(exc)
        return context
