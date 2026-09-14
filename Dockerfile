FROM python:3.11-slim

WORKDIR /app

# System deps needed to build psycopg2 if a wheel isn't available for the arch
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY frontend ./frontend

# Render (and most PaaS) inject PORT at runtime; default to 8000 for local/docker-compose use.
ENV PORT=8000
EXPOSE 8000

# Shell form so $PORT is expanded at container start.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
