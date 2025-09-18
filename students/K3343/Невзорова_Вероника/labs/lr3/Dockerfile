FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements ./
RUN pip install --no-cache-dir -r requirements

COPY app ./app
COPY infrastructure ./infra

CMD ["uvicorn", "app.main_api:api", "--host", "0.0.0.0", "--port", "8000"]