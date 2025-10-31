# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/app/.mplconfig

WORKDIR /app

RUN adduser \
        --disabled-password \
        --gecos "" \
        --home "/nonexistent" \
        --shell "/usr/sbin/nologin" \
        --no-create-home \
        appuser

COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/.mplconfig && chown appuser:appuser /app/.mplconfig

COPY . .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/')\"

CMD ["python", "-m", "http.server", "8000"]
