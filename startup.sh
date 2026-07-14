#!/bin/bash
set -euo pipefail

# SQLite persistence on Azure App Service (Linux):
# /home is the only persistent, shared storage. If DB_NAME points at a path
# under the ephemeral app root (e.g. default BASE_DIR/db.sqlite3), the
# database is wiped on restart/redeploy. Point DB_NAME under /home (via App
# Settings) for data to survive. This is a known limitation pending the
# planned MSSQL migration — do not change the engine here.

# Do not export/override DJANGO_SETTINGS_MODULE here — ops owns it via Azure
# App Settings. But manage.py and wsgi.py setdefault to
# statzcorp.settings.local (DEBUG=True, console email). Refuse to start
# unless production settings are explicitly configured.
if [[ "${DJANGO_SETTINGS_MODULE:-}" != "statzcorp.settings.production" ]]; then
    echo "ERROR: DJANGO_SETTINGS_MODULE must be 'statzcorp.settings.production' (got '${DJANGO_SETTINGS_MODULE:-<unset>}')." >&2
    echo "       Set it under App Service → Configuration → Application Settings." >&2
    echo "       Refusing to start: unset/wrong values fall back to local settings (DEBUG=True)." >&2
    exit 1
fi

echo "=== STATZ Corp: starting deployment tasks ==="
echo "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}"

# Ensure persistent SQLite parent dir exists when DB_NAME is under /home.
# Safe no-op if unused; avoids migrate() failing on a fresh App Service
# instance where /home/data does not exist yet.
mkdir -p /home/data

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Launching gunicorn..."
exec gunicorn statzcorp.wsgi:application \
    --bind=0.0.0.0:${PORT:-8000} \
    --workers=4 \
    --timeout=600 \
    --access-logfile '-' \
    --error-logfile '-'
