#!/bin/bash
export PYTHONPATH="/app${PYTHONPATH:+:$PYTHONPATH}"
uv run celery -A auth_app.core.celery_app.celery_app worker --loglevel=info
