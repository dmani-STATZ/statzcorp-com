from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import SupplierPortalAccount

GENERIC_ERROR = "Invalid CAGE code or password."
LOCKED_ERROR = "This account is temporarily locked due to repeated failed attempts. Please try again later."
NO_ACCOUNT_ERROR = (
    "We couldn't find a Supplier Portal account for that CAGE code. "
    "If you believe your company should have access, please contact us at "
    "info@statzcorp.com or 608-798-4500."
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
    """Step 1 of request-access / forgot-password: identify the account by CAGE code."""

    cage_code = forms.CharField(label='CAGE Code', max_length=10)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.account = None

    def clean_cage_code(self):
        code = self.cleaned_data['cage_code'].strip().upper()
        try:
            self.account = SupplierPortalAccount.objects.get(cage_code=code, is_active=True)
        except SupplierPortalAccount.DoesNotExist:
            raise forms.ValidationError(NO_ACCOUNT_ERROR)
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
