from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    # Spam honeypot field
    website = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
        label='Leave blank'
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
        honeypot = cleaned_data.get('website')
        if honeypot:
            # Silently fail or raise validation error to stop submission
            raise forms.ValidationError("Spam detected.")
        return cleaned_data
