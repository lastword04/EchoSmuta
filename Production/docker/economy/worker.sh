#!/bin/bash
uv run celery -A mining_app.core.celery_app.celery_app worker --loglevel=debug
