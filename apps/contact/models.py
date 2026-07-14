from django.db import models

class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'

    def __str__(self):
        return f"Message from {self.name} ({self.company or 'No Company'}) on {self.created_at.strftime('%Y-%m-%d')}"


class ContactRecipient(models.Model):
    email = models.EmailField(unique=True)
    label = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional note, e.g. 'HR', 'Owner', 'Sales Lead' — for admin reference only."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to stop sending contact form notifications to this address without deleting it."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['email']
        verbose_name = 'Contact Notification Recipient'
        verbose_name_plural = 'Contact Notification Recipients'

    def __str__(self):
        return f"{self.email} ({self.label})" if self.label else self.email
