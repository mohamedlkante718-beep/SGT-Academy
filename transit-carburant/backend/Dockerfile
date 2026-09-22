FROM python:3.11-slim

WORKDIR /app

# psycopg2-binary a besoin de libpq au runtime (pas seulement au build).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --create-home appuser \
    && mkdir -p /app/media \
    && chown -R appuser:appuser /app
USER appuser

ENV MEDIA_ROOT=/app/media

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
