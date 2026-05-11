# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
COPY scripts ./scripts
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts/docker-entrypoint.sh /docker-entrypoint.sh

RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir . \
    && chmod +x /docker-entrypoint.sh \
    && useradd --uid 10001 --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app /docker-entrypoint.sh

EXPOSE 8000

USER appuser

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
