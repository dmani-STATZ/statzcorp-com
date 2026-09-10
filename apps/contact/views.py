import time

from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.contrib import messages
from django.core import signing
from django.core.mail import send_mail
from django.conf import settings

from .forms import ContactForm, HUMAN_VERIFICATION_ERROR
from .models import ContactRecipient
from .spam import defang_urls, score_submission


class ContactUsView(FormView):
    template_name = 'contact/contact-us.html'
    form_class = ContactForm
    success_url = '/contact-us/'

    def get_initial(self):
        initial = super().get_initial()
        initial['ts'] = signing.dumps(int(time.time()), salt='contact-form-render')
        return initial

    def get_recipient_list(self):
        """
        Returns the live list of active contact notification recipients.
        Queried fresh on every call — no caching, so admin changes to
        ContactRecipient take effect immediately without an app restart.
        Falls back to settings.CONTACT_EMAIL_TO if no active recipients exist.
        """
        active_emails = list(
            ContactRecipient.objects.filter(is_active=True).values_list('email', flat=True)
        )
        if active_emails:
            return active_emails

        import logging
        logger = logging.getLogger('apps')
        logger.warning(
            "No active ContactRecipient rows found — falling back to settings.CONTACT_EMAIL_TO. "
            "Configure recipients in Django admin under Contact > Contact Notification Recipients."
        )
        return settings.CONTACT_EMAIL_TO

    def form_valid(self, form):
        message_obj = form.save(commit=False)
        score, reasons = score_submission(
            name=form.cleaned_data['name'],
            company=form.cleaned_data.get('company') or '',
            email=form.cleaned_data['email'],
            phone=form.cleaned_data['phone'],
            message=form.cleaned_data['message'],
        )
        message_obj.spam_score = score
        message_obj.is_flagged = score >= 4
        message_obj.flag_reasons = reasons
        message_obj.save()

        if message_obj.is_flagged:
            messages.success(self.request, "Thank you! Your message has been received. We will be in touch shortly.")
            return super().form_valid(form)

        safe_name = defang_urls(message_obj.name)
        safe_company = defang_urls(message_obj.company or 'N/A')
        safe_email = defang_urls(message_obj.email)
        safe_phone = defang_urls(message_obj.phone)
        safe_message = defang_urls(message_obj.message)

        subject = f"[STATZ Web Contact] New Message from {safe_name}"
        body = (
            f"New contact form submission:\n"
            f"=================================\n"
            f"Name:    {safe_name}\n"
            f"Company: {safe_company}\n"
            f"Email:   {safe_email}\n"
            f"Phone:   {safe_phone}\n"
            f"=================================\n\n"
            f"{safe_message}\n\n"
            f"Links above have been defanged. Do not re-enable and open them.\n"
        )

        recipient_list = self.get_recipient_list()

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            messages.success(self.request, "Thank you! Your message has been received. We will be in touch shortly.")
        except Exception as e:
            import logging
            logger = logging.getLogger('apps')
            logger.error(f"Email sending failed: {e}")
            messages.warning(self.request, "Your message was saved, but we couldn't send an email notification. We will still review it shortly.")

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, HUMAN_VERIFICATION_ERROR)
        return super().form_invalid(form)
