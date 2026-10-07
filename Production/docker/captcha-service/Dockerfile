FROM python:3.10-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./services/captcha-service .

RUN uv sync --frozen

COPY ./Production/docker/captcha-service/entrypoint.sh /docker/entrypoint.sh

RUN chmod +x /docker/entrypoint.sh
