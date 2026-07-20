from django import forms

from .models import SupplierPortalAccount

GENERIC_ERROR = "Invalid CAGE code or password."
LOCKED_ERROR = "This account is temporarily locked due to repeated failed attempts. Please try again later."


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
