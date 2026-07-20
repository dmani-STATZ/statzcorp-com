import logging

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from .tokens import make_set_password_token

logger = logging.getLogger('apps')


def mask_email(email):
    """j***@a***.com — recognizable to the owner, useless to a stranger."""
    local, _, domain = email.partition('@')
    domain_name, dot, tld = domain.rpartition('.')
    if domain_name:
        return f"{local[:1]}***@{domain_name[:1]}***{dot}{tld}"
    return f"{local[:1]}***@{domain[:1]}***"


def send_set_password_link(request, account):
    """
    Emails a one-hour set-password link to the account's on-file address.
    Returns True on success. Raises nothing — failures are logged and
    reported via the return value so callers can show an honest message.
    """
    token = make_set_password_token(account)
    url = request.build_absolute_uri(
        reverse('supplier_portal:set_password', kwargs={'token': token})
    )
    subject = "STATZ Supplier Portal — set your password"
    body = (
        f"A password setup was requested for the STATZ Supplier Portal account "
        f"for CAGE code {account.cage_code}.\n\n"
        f"Use the link below to choose your password. The link expires in 1 hour "
        f"and can only be used once:\n\n"
        f"{url}\n\n"
        f"If you did not request this, you can ignore this email — nothing has "
        f"changed on your account.\n\n"
        f"Questions, or is this the wrong contact address for your company? "
        f"Contact STATZ Corporation at info@statzcorp.com or 608-798-4500.\n"
    )
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[account.contact_email],
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception(
            "Supplier Portal: failed to send set-password email for CAGE %s",
            account.cage_code,
        )
        return False
