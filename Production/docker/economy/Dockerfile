FROM python:3.10-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./services/economy .

RUN uv sync --frozen

COPY ./Production/docker/scripts/wait-for-it.sh /usr/local/bin/
COPY ./Production/docker/economy/entrypoint.sh /docker/entrypoint.sh
COPY ./Production/docker/economy/worker.sh /docker/worker.sh


RUN chmod +x /docker/entrypoint.sh \
    && chmod +x /usr/local/bin/wait-for-it.sh \
    && chmod +x /docker/worker.sh

