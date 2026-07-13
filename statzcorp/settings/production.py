from .base import *

# Production settings for Azure Web App (GCCH)
DEBUG = False

# Security settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Database: SQLite is current (configured in base.py via DB_* / defaults).
# Plan: migrate to Microsoft SQL Server (MSSQL) later — do not introduce PostgreSQL.
# When switching to MSSQL, install mssql-django + pyodbc and set DB_ENGINE/OPTIONS
# (ODBC driver, Encrypt, TrustServerCertificate, etc.) under human direction.
