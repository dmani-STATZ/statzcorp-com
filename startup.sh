#!/bin/bash
set -euo pipefail

# SQLite persistence on Azure App Service (Linux):
# /home is the only persistent, shared storage. If DB_NAME points at a path
# under the ephemeral app root (e.g. default BASE_DIR/db.sqlite3), the
# database is wiped on restart/redeploy. Point DB_NAME under /home (via App
# Settings) for data to survive. This is a known limitation pending the
# planned MSSQL migration — do not change the engine here.

echo "=== STATZ Corp: starting deployment tasks ==="

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
