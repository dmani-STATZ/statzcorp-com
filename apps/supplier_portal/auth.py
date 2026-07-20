"""
Session-based auth for the Supplier Portal — intentionally not
django.contrib.auth. Suppliers aren't staff users and shouldn't share a
session/identity system with /admin/; this stores just an account id under
its own session key.
"""
from .models import SupplierPortalAccount

SESSION_KEY = 'supplier_portal_account_id'


def login_supplier(request, account):
    request.session[SESSION_KEY] = account.pk
    request.session.cycle_key()  # rotate session id on privilege change
    account.reset_failed_attempts()
    account.register_login()


def logout_supplier(request):
    request.session.pop(SESSION_KEY, None)


def get_current_account(request):
    account_id = request.session.get(SESSION_KEY)
    if not account_id:
        return None
    try:
        return SupplierPortalAccount.objects.get(pk=account_id, is_active=True)
    except SupplierPortalAccount.DoesNotExist:
        return None
