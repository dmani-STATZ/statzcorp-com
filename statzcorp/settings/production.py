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

# Database: production inherits the config-driven SQLite default from base.py.
# Do not hardcode ENGINE='mssql' (or any DATABASES override) here until both
# blockers below are resolved.
#
# MSSQL attempt 2026-07-14 — PAUSED / REVERTED (not abandoned):
#   1. Microsoft ODBC Driver 18 is not present on the App Service Linux
#      Python base image and does not persist across container restarts.
#      Need a durable install strategy (e.g. startup.sh apt-get bootstrap or
#      a custom Docker image) before mssql-django / pyodbc can work.
#   2. The target DB host is a private IP requiring VNet Integration on the
#      App Service, which is not yet configured — the app cannot reach the
#      server even if the ODBC driver were present.
# When resuming: install/uncomment mssql-django + pyodbc, set DB_ENGINE /
# DB_* / ODBC OPTIONS under human direction, and clear Azure App Settings
# that still point DB_HOST/USER/PASSWORD at the private MSSQL IP if staying
# on SQLite in the meantime.
#
# SQLite on Azure: point DB_NAME under /home (e.g. /home/data/db.sqlite3)
# via App Settings. Linux App Service only persists /home; the default
# BASE_DIR/db.sqlite3 is ephemeral and is lost on every restart/redeploy.
# See AGENTS.md Known Gotchas and startup.sh (mkdir -p /home/data).
