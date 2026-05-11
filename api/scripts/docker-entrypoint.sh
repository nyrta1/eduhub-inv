#!/usr/bin/env sh
set -eu

echo "Applying database migrations..."
alembic upgrade head

exec "$@"