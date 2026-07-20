from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import SupplierPortalAccount
from .statzweb_client import StatzWebAPIError, verify_supplier

GENERIC_ERROR = "Invalid CAGE code or password."
LOCKED_ERROR = "This account is temporarily locked due to repeated failed attempts. Please try again later."
NO_ACCOUNT_ERROR = (
    "We couldn't find a Supplier Portal account for that CAGE code. "
    "If you believe your company should have access, please contact us at "
    "info@statzcorp.com or 608-798-4500."
)
NO_CONTACT_EMAIL_ERROR = (
    "We found your company, but don't have a contact email on file to send a link to. "
    "Please contact us at info@statzcorp.com or 608-798-4500 so we can add one."
)
SERVICE_UNAVAILABLE_ERROR = (
    "We couldn't reach the supplier lookup service just now. Please try again shortly, "
    "or contact us at info@statzcorp.com or 608-798-4500."
)


class SupplierLoginForm(forms.Form):
    cage_code = forms.CharField(label='CAGE Code', max_length=10)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.account = None

    def clean(self):
        cleaned = super().clean()
        cage_code = cleaned.get('cage_code')
        password = cleaned.get('password')
        if not cage_code or not password:
            return cleaned

        try:
            account = SupplierPortalAccount.objects.get(cage_code__iexact=cage_code.strip())
        except SupplierPortalAccount.DoesNotExist:
            raise forms.ValidationError(GENERIC_ERROR)

        if not account.is_active:
            raise forms.ValidationError(GENERIC_ERROR)

        if account.is_locked():
            raise forms.ValidationError(LOCKED_ERROR)

        if not account.check_password(password):
            account.register_failed_attempt()
            raise forms.ValidationError(GENERIC_ERROR)

        self.account = account
        return cleaned


class RequestAccessForm(forms.Form):
    """
    Step 1 of request-access / forgot-password: identify the supplier by CAGE
    code. Looks the CAGE code up live in STATZWeb (source of truth for the
    contact email) and auto-provisions/refreshes the local
    SupplierPortalAccount from that response — there's no separate staff
    "create the account" step for a supplier that already exists in STATZWeb.
    """

    cage_code = forms.CharField(label='CAGE Code', max_length=10)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.account = None

    def clean_cage_code(self):
        code = self.cleaned_data['cage_code'].strip().upper()

        try:
            data = verify_supplier(code)
        except StatzWebAPIError:
            raise forms.ValidationError(SERVICE_UNAVAILABLE_ERROR)

        if not data or not data.get('is_active', True):
            raise forms.ValidationError(NO_ACCOUNT_ERROR)

        contact_email = (data.get('contact_email') or '').strip()
        if not contact_email:
            raise forms.ValidationError(NO_CONTACT_EMAIL_ERROR)

        account, _ = SupplierPortalAccount.objects.get_or_create(
            cage_code=code,
            defaults={'contact_email': contact_email},
        )
        if not account.is_active:
            raise forms.ValidationError(NO_ACCOUNT_ERROR)
        if account.contact_email != contact_email:
            account.contact_email = contact_email
            account.save(update_fields=['contact_email', 'updated_at'])

        self.account = account
        return code


class SetPasswordForm(forms.Form):
    password1 = forms.CharField(label='New password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm new password', widget=forms.PasswordInput)

    def clean_password1(self):
        password = self.cleaned_data['password1']
        validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('password1'), cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("The two passwords don't match.")
        return cleaned
