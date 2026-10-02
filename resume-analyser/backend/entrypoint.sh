#!/bin/sh
set -e

echo "Running database migrations..."
if [ "${AUTO_CREATE_TABLES}" = "true" ] && [ -z "${DATABASE_URL#*sqlite*}" ]; then
    # Dev convenience: SQLite + auto-create. No Alembic needed.
    python -c "from app.db.database import init_db; init_db()"
else
    # Production path: always migrate via Alembic (works for Postgres and SQLite).
    alembic upgrade head
fi

echo "Starting server..."
exec gunicorn main:app \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8000 \
    -w "${WEB_CONCURRENCY:-2}" \
    --timeout 120 \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile -
