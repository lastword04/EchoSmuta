#!/bin/bash
uv run granian file_storage_app.main:app --interface asgi --host :: --port 9094 --reload
