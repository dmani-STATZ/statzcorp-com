import logging

from django.urls import reverse
from django.utils.html import escape

from .statzweb_client import StatzWebAPIError, send_email as statzweb_send_email
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

    Routed through STATZWeb's Graph-based send-email API
    (statzweb_client.send_email), not Django's SMTP send_mail — GCCH direct
    send generally can't deliver to external supplier addresses, and
    STATZWeb already has a working Graph mail integration for exactly this.

    Returns True on success. Raises nothing — failures are logged and
    reported via the return value so callers can show an honest message.
    """
    token = make_set_password_token(account)
    url = request.build_absolute_uri(
        reverse('supplier_portal:set_password', kwargs={'token': token})
    )
    subject = "STATZ Supplier Portal — set your password"
    cage_code = escape(account.cage_code)
    body_html = (
        f"<p>A password setup was requested for the STATZ Supplier Portal account "
        f"for CAGE code {cage_code}.</p>"
        f"<p>Use the link below to choose your password. The link expires in 1 hour "
        f"and can only be used once:</p>"
        f'<p><a href="{escape(url)}">{escape(url)}</a></p>'
        f"<p>If you did not request this, you can ignore this email — nothing has "
        f"changed on your account.</p>"
        f"<p>Questions, or is this the wrong contact address for your company? "
        f"Contact STATZ Corporation at "
        f'<a href="mailto:info@statzcorp.com">info@statzcorp.com</a> or 608-798-4500.</p>'
    )
    try:
        statzweb_send_email(account.contact_email, subject, body_html)
        return True
    except StatzWebAPIError:
        logger.exception(
            "Supplier Portal: failed to send set-password email for CAGE %s",
            account.cage_code,
        )
        return False
