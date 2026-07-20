"""
STATZ Corporation — Base Django Settings
Shared across all environments. Do not put secrets here.
"""
from pathlib import Path
from decouple import config, Csv

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY = config('DJANGO_SECRET_KEY')
DEBUG      = config('DJANGO_DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ── Application definition ────────────────────────────────────────────────────
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'storages',  # django-storages — Azure Blob backend when AZURE_CONNECTION_STRING is set
]

LOCAL_APPS = [
    'apps.public',
    'apps.contact',
    'apps.surveys',
    'apps.videos',
    'apps.supplier_portal',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ── Middleware ────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',      # Serve static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'statzcorp.urls'

# ── Templates ─────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'statzcorp.wsgi.application'

# ── Database ──────────────────────────────────────────────────────────────────
# Current: SQLite (default). Planned later: Microsoft SQL Server (MSSQL).
# Do not use PostgreSQL in this project.
DATABASES = {
    'default': {
        'ENGINE':   config('DB_ENGINE',   default='django.db.backends.sqlite3'),
        'NAME':     config('DB_NAME',     default=str(BASE_DIR / 'db.sqlite3')),
        'USER':     config('DB_USER',     default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST':     config('DB_HOST',     default=''),
        'PORT':     config('DB_PORT',     default=''),
    }
}

# ── Auth password validation ──────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Internationalisation ──────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'America/Chicago'
USE_I18N      = True
USE_TZ        = True

# ── Static files ──────────────────────────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'          # collectstatic output
STATICFILES_DIRS = [BASE_DIR / 'static']        # source files

# WhiteNoise: compress & cache static files without a CDN
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
}

# ── Media files (user uploads) ────────────────────────────────────────────────
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Azure Blob Storage (Azure Government / GCCH) — optional.
# Leave AZURE_CONNECTION_STRING blank for local FileSystemStorage.
# Never log or commit the connection string. The connection string encodes
# the GCCH endpoint suffix (core.usgovcloudapi.net); do not set account
# name/key separately.
AZURE_CONNECTION_STRING = config('AZURE_CONNECTION_STRING', default='')
AZURE_CONTAINER = config('AZURE_CONTAINER', default='media')
AZURE_OVERWRITE_FILES = False
AZURE_LOCATION = 'media'

if AZURE_CONNECTION_STRING:
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.azure_storage.AzureStorage',
    }

# Large media uploads (videos) via Django admin
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 1024      # 1 GB request cap
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024        # >10 MB streams to temp file

# ── Default primary key ───────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Email ─────────────────────────────────────────────────────────────────────
EMAIL_BACKEND       = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST          = config('EMAIL_HOST',    default='smtp.office365.com')
EMAIL_PORT          = config('EMAIL_PORT',    default=587, cast=int)
EMAIL_USE_TLS       = config('EMAIL_USE_TLS', default=True,  cast=bool)
EMAIL_HOST_USER     = config('EMAIL_HOST_USER',     default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL',  default='noreply@statzcorp.com')
CONTACT_EMAIL_TO = [
    addr.strip()
    for addr in config('CONTACT_EMAIL_TO', default='info@statzcorp.com').split(',')
    if addr.strip()
]

# ── Supplier Portal → STATZWeb API (Phase 1b) ─────────────────────────────────
# Server-to-server only. Contract: docs/supplier-portal-api-contract.md
# SUPPLIER_PORTAL_API_KEY / SUPPLIER_PORTAL_HMAC_SECRET must match the values
# configured in STATZWeb's own environment. Never logged, never sent to a client.
SUPPLIER_PORTAL_API_BASE_URL = config('SUPPLIER_PORTAL_API_BASE_URL', default='')
SUPPLIER_PORTAL_API_KEY = config('SUPPLIER_PORTAL_API_KEY', default='')
SUPPLIER_PORTAL_HMAC_SECRET = config('SUPPLIER_PORTAL_HMAC_SECRET', default='')

# ── Logging ───────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('DJANGO_LOG_LEVEL', default='WARNING'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
