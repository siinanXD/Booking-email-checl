#!/bin/sh
set -e

if [ -n "${ADMIN_EMAIL:-}" ] && [ -n "${ADMIN_PASSWORD:-}" ]; then
  python scripts/seed_admin.py || true
fi

exec "$@"
