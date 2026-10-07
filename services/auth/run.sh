#!/bin/bash
uv run granian auth_app.main:app --interface asgi --host :: --port 9090 --reload
