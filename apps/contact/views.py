from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import ContactForm

class ContactUsView(FormView):
    template_name = 'contact/contact-us.html'
    form_class = ContactForm
    success_url = '/contact-us/'

    def form_valid(self, form):
        # Save to database
        message_obj = form.save()

        # Build email content
        subject = f"[STATZ Web Contact] New Message from {message_obj.name}"
        body = (
            f"New contact form submission:\n"
            f"=================================\n"
            f"Name:    {message_obj.name}\n"
            f"Company: {message_obj.company or 'N/A'}\n"
            f"Email:   {message_obj.email}\n"
            f"Phone:   {message_obj.phone}\n"
            f"=================================\n\n"
            f"{message_obj.message}\n"
        )

        try:
            # Send notification email
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL_TO],
                fail_silently=False,
            )
            messages.success(self.request, "Thank you! Your message has been received. We will be in touch shortly.")
        except Exception as e:
            # Log error
            import logging
            logger = logging.getLogger('apps')
            logger.error(f"Email sending failed: {e}")
            messages.warning(self.request, "Your message was saved, but we couldn't send an email notification. We will still review it shortly.")

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors in the form below.")
        return super().form_invalid(form)
