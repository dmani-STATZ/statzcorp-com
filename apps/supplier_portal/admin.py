from django.contrib import admin, messages

from .emails import send_set_password_link
from .models import SupplierPortalAccount


@admin.register(SupplierPortalAccount)
class SupplierPortalAccountAdmin(admin.ModelAdmin):
    """
    Staff creates accounts with a CAGE code and contact email only.
    Passwords are never set or seen here — suppliers set their own via
    the emailed set-password link (self-service on the login page, or
    the "Email a set-password link" action below).
    """

    list_display = ('cage_code', 'contact_email', 'is_active', 'password_is_set', 'account_locked', 'last_login')
    list_filter = ('is_active',)
    search_fields = ('cage_code', 'contact_email')
    readonly_fields = ('failed_attempts', 'locked_until', 'last_login', 'last_reset_request_at', 'created_at', 'updated_at')
    actions = ['send_password_link']
    fieldsets = (
        (None, {'fields': ('cage_code', 'contact_email', 'is_active')}),
        ('Login status', {'fields': ('failed_attempts', 'locked_until', 'last_login', 'last_reset_request_at')}),
        ('Audit', {'fields': ('created_at', 'updated_at')}),
    )

    @admin.display(boolean=True, description='Password set')
    def password_is_set(self, obj):
        return obj.has_usable_password()

    @admin.display(boolean=True, description='Locked')
    def account_locked(self, obj):
        return obj.is_locked()

    @admin.action(description='Email a set-password link to the on-file address')
    def send_password_link(self, request, queryset):
        sent, failed = 0, 0
        for account in queryset:
            if not account.is_active:
                failed += 1
                continue
            if send_set_password_link(request, account):
                account.register_reset_request()
                sent += 1
            else:
                failed += 1
        if sent:
            self.message_user(request, f"Set-password link emailed for {sent} account(s).")
        if failed:
            self.message_user(
                request,
                f"{failed} account(s) skipped (inactive) or failed to send — check logs.",
                level=messages.WARNING,
            )
