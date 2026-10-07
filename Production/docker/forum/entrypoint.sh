#!/bin/bash
/usr/local/bin/wait-for-it.sh production-forum-service-db:5432 --timeout=30 --strict -- echo "Database is up and ready"

echo "Run Alembic migrations..."
uv run alembic upgrade head

echo "Starting FastAPI application..."
uv run granian forum_app.main:app --interface asgi --host 0.0.0.0 --port 8086
