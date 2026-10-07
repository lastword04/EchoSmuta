#!/bin/bash
echo "Starting FastAPI application..."
uv run granian captcha_app.main:app --interface asgi --host 0.0.0.0 --port 8085
