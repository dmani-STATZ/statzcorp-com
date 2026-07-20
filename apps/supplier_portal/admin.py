from django import forms
from django.contrib import admin

from .models import SupplierPortalAccount


class SupplierPortalAccountAdminForm(forms.ModelForm):
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        help_text="Leave blank to keep the current password. Set here to create the account or reset a forgotten password.",
    )

    class Meta:
        model = SupplierPortalAccount
        fields = ['cage_code', 'contact_email', 'is_active', 'new_password']

    def save(self, commit=True):
        account = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            account.set_password(new_password)
        if commit:
            account.save()
        return account


@admin.register(SupplierPortalAccount)
class SupplierPortalAccountAdmin(admin.ModelAdmin):
    form = SupplierPortalAccountAdminForm
    list_display = ('cage_code', 'contact_email', 'is_active', 'account_locked', 'last_login')
    list_filter = ('is_active',)
    search_fields = ('cage_code', 'contact_email')
    readonly_fields = ('failed_attempts', 'locked_until', 'last_login', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('cage_code', 'contact_email', 'is_active', 'new_password')}),
        ('Login status', {'fields': ('failed_attempts', 'locked_until', 'last_login')}),
        ('Audit', {'fields': ('created_at', 'updated_at')}),
    )

    @admin.display(boolean=True, description='Locked')
    def account_locked(self, obj):
        return obj.is_locked()
