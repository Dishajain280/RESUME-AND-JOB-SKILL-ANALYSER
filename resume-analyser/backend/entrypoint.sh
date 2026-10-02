#!/bin/sh
set -e

echo "Starting server..."
exec gunicorn main:app \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8000 \
    -w "${WEB_CONCURRENCY:-2}" \
    --timeout 120 \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile -
