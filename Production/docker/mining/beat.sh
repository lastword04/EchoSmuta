#!/bin/bash
export PYTHONPATH="/app${PYTHONPATH:+:$PYTHONPATH}"
uv run celery -A mining_app.core.celery_app.celery_app beat --loglevel=debug
