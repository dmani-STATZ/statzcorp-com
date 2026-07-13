from .base import *

# Local development settings
DEBUG = True

# SQLite is the active database (defaults in base.py / .env).
# You can override settings here specifically for local development.

# Log emails to the console instead of trying to send them
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
