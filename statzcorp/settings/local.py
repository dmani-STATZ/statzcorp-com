from .base import *

# Local development settings
DEBUG = True

# SQLite local database is set in base.py by default if env vars aren't provided.
# You can override settings here specifically for local development.

# Log emails to the console instead of trying to send them
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
