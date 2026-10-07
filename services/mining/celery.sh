#!/bin/bash
uv run celery -A mining_app.core.celery_app.celery_app worker --loglevel=debug --without-gossip --without-mingle --without-heartbeat --soft-time-limit=300 --time-limit=360
