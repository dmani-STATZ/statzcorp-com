import logging

from django.contrib.auth.forms import PasswordResetForm
from django.template.loader import render_to_string

from apps.supplier_portal.statzweb_client import send_email

logger = logging.getLogger('apps')


class StatzPasswordResetForm(PasswordResetForm):
    """Send Django's standard reset token through STATZWeb Graph mail."""

    def get_users(self, email):
        return (user for user in super().get_users(email) if user.is_staff)

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        subject = render_to_string(subject_template_name, context)
        subject = ''.join(subject.splitlines())
        body_template = (
            html_email_template_name
            or 'accounts/email/password_reset_email.html'
        )
        body_html = render_to_string(body_template, context)

        try:
            send_email(
                to=to_email,
                subject=subject,
                body_html=body_html,
            )
        except Exception:
            # Preserve Django's enumeration-safe response for matched and
            # unmatched addresses while retaining server-side diagnostics.
            logger.exception('Failed to send a staff password-reset email')
