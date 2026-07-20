from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone

LOCKOUT_THRESHOLD = 5
LOCKOUT_DURATION = timedelta(minutes=15)


class SupplierPortalAccount(models.Model):
    """
    Login credential for the public-site Supplier Portal.

    Deliberately separate from django.contrib.auth.User: this identifies a
    supplier company (by CAGE code), not a staff/admin identity, and one
    account is shared by everyone at that supplier. Supplier business data
    itself is never stored here — it's fetched live from the STATZWeb API
    (see docs/supplier-portal-api-contract.md); this model only gatekeeps
    the portal login.
    """

    cage_code = models.CharField(max_length=10, unique=True)
    password = models.CharField(max_length=128, editable=False)
    contact_email = models.EmailField(
        help_text="Where password-reset / provisioning links are sent. Not used as a login field."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to block portal login without deleting the account.",
    )
    failed_attempts = models.PositiveIntegerField(default=0, editable=False)
    locked_until = models.DateTimeField(null=True, blank=True, editable=False)
    last_login = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Supplier Portal Account'
        verbose_name_plural = 'Supplier Portal Accounts'
        ordering = ['cage_code']

    def __str__(self):
        return self.cage_code

    def save(self, *args, **kwargs):
        if self.cage_code:
            self.cage_code = self.cage_code.strip().upper()
        if not self.password:
            self.password = make_password(None)  # unusable until staff sets one
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())

    def register_failed_attempt(self):
        self.failed_attempts += 1
        if self.failed_attempts >= LOCKOUT_THRESHOLD:
            self.locked_until = timezone.now() + LOCKOUT_DURATION
        self.save(update_fields=['failed_attempts', 'locked_until', 'updated_at'])

    def reset_failed_attempts(self):
        if self.failed_attempts or self.locked_until:
            self.failed_attempts = 0
            self.locked_until = None
            self.save(update_fields=['failed_attempts', 'locked_until', 'updated_at'])

    def register_login(self):
        self.last_login = timezone.now()
        self.save(update_fields=['last_login', 'updated_at'])
