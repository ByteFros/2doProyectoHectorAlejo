#!/bin/sh

set -eu

DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
PORT=${PORT:-8000}
RUN_MIGRATIONS=${RUN_MIGRATIONS:-true}
RUN_COLLECTSTATIC=${RUN_COLLECTSTATIC:-true}
SEED_INITIAL_USERS=${SEED_INITIAL_USERS:-false}
GUNICORN_WORKERS=${GUNICORN_WORKERS:-3}
GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-60}
EXTRA_MANAGEMENT_COMMANDS=${EXTRA_MANAGEMENT_COMMANDS:-}

echo "Starting backend in ${DJANGO_ENV:-development} mode"

if [ "$RUN_COLLECTSTATIC" = "true" ]; then
  echo "Collecting static files"
  python manage.py collectstatic --no-input
else
  echo "Skipping collectstatic step"
fi

if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo "Waiting for database ${DB_HOST}:${DB_PORT}"
  ./wait-for-it.sh "${DB_HOST}" "${DB_PORT}" python manage.py migrate --no-input
else
  echo "Skipping migrate step"
  ./wait-for-it.sh "${DB_HOST}" "${DB_PORT}" echo "Database reachable"
fi

if [ "$SEED_INITIAL_USERS" = "true" ]; then
  echo "Seeding initial role users"
  python manage.py create_test_users
else
  echo "Skipping initial user seeding"
fi

if [ -n "$EXTRA_MANAGEMENT_COMMANDS" ]; then
  echo "Running extra management commands"
  printf '%s\n' "$EXTRA_MANAGEMENT_COMMANDS" | tr ';' '\n' | while IFS= read -r raw_cmd; do
    cmd=$(printf '%s' "$raw_cmd" | xargs)
    if [ -z "$cmd" ]; then
      continue
    fi
    echo "→ python manage.py $cmd"
    python manage.py $cmd
  done
else
  echo "No extra management commands configured"
fi

echo "Launching Gunicorn on port ${PORT}"
exec gunicorn administrador.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers "${GUNICORN_WORKERS}" \
  --timeout "${GUNICORN_TIMEOUT}"
