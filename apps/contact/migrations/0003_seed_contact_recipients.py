from django.db import migrations
from decouple import config


def seed_recipients(apps, schema_editor):
    ContactRecipient = apps.get_model('contact', 'ContactRecipient')
    raw = config('CONTACT_EMAIL_TO', default='info@statzcorp.com')
    addresses = [addr.strip() for addr in raw.split(',') if addr.strip()]
    for addr in addresses:
        ContactRecipient.objects.get_or_create(email=addr, defaults={'label': 'Seeded from CONTACT_EMAIL_TO'})


def reverse_noop(apps, schema_editor):
    pass  # Intentionally not reversing — do not delete admin-managed data on rollback.


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0002_contactrecipient'),
    ]

    operations = [
        migrations.RunPython(seed_recipients, reverse_noop),
    ]
