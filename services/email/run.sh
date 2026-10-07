#!/bin/bash
uv run granian --interface asgi notification_email_service.main:app  --host :: --port 9093 --reload

