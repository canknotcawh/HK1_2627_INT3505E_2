#!/bin/sh
set -eu
# For this teaching lab, create missing tables automatically on first startup.
# For production, replace this with reviewed Alembic migrations.
flask --app wsgi:app init-db
exec gunicorn -c gunicorn.conf.py wsgi:app
