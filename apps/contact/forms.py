import time

from django import forms
from django.core import signing
from django_altcha import AltchaField

from .models import ContactMessage


HUMAN_VERIFICATION_ERROR = "Please complete the human verification check and try again."


class ContactForm(forms.ModelForm):
    url = forms.CharField(
        required=False,
        label='Website URL',
        widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}),
    )
    subject = forms.CharField(
        required=False,
        label='Message Subject',
        widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}),
    )
    ts = forms.CharField(required=False, widget=forms.HiddenInput)
    altcha = AltchaField(
        label='Human verification',
        error_messages={
            'error': HUMAN_VERIFICATION_ERROR,
            'invalid': HUMAN_VERIFICATION_ERROR,
            'required': HUMAN_VERIFICATION_ERROR,
            'replay': HUMAN_VERIFICATION_ERROR,
        },
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'company', 'email', 'phone', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your Name *', 'required': 'true'}),
            'company': forms.TextInput(attrs={'placeholder': 'Company Name (if applicable)'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address *', 'required': 'true'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number *', 'required': 'true'}),
            'message': forms.Textarea(attrs={'placeholder': 'Comments and/or Questions *', 'required': 'true', 'rows': 6}),
        }

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('url') or cleaned_data.get('subject'):
            raise forms.ValidationError(HUMAN_VERIFICATION_ERROR)

        try:
            rendered_at = signing.loads(
                cleaned_data.get('ts', ''),
                salt='contact-form-render',
                max_age=7200,
            )
            elapsed = time.time() - int(rendered_at)
        except (signing.BadSignature, TypeError, ValueError):
            raise forms.ValidationError(HUMAN_VERIFICATION_ERROR)

        if elapsed < 3:
            raise forms.ValidationError(HUMAN_VERIFICATION_ERROR)

        return cleaned_data
