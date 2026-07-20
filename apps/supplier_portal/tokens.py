"""
Signed, time-limited set-password tokens for the Supplier Portal.

The token embeds a fragment of the account's current password hash, so
every outstanding token dies the moment a new password is set — a link
can only be used once even within its time window.
"""
from django.core import signing

SET_PASSWORD_SALT = 'supplier-portal-set-password'
SET_PASSWORD_MAX_AGE = 60 * 60  # 1 hour


def make_set_password_token(account):
    return signing.dumps(
        {'pk': account.pk, 'pw': account.password[-12:]},
        salt=SET_PASSWORD_SALT,
    )


def read_set_password_token(token):
    """Returns the active account for a valid token, else None."""
    from .models import SupplierPortalAccount

    try:
        data = signing.loads(token, salt=SET_PASSWORD_SALT, max_age=SET_PASSWORD_MAX_AGE)
    except signing.BadSignature:
        return None
    try:
        account = SupplierPortalAccount.objects.get(pk=data.get('pk'), is_active=True)
    except SupplierPortalAccount.DoesNotExist:
        return None
    if account.password[-12:] != data.get('pw'):
        return None
    return account
