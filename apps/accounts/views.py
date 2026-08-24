from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from .forms import StatzPasswordResetForm


class StaffPasswordResetView(auth_views.PasswordResetView):
    form_class = StatzPasswordResetForm
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/email/password_reset_email.html'
    html_email_template_name = 'accounts/email/password_reset_email.html'
    subject_template_name = 'accounts/email/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')


class StaffPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class StaffPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class StaffPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'
