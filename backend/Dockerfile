FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DJANGO_ENV=prod

EXPOSE 8000
# migrate + collectstatic tournent au démarrage (pas au build) car ils
# nécessitent DATABASE_URL/SECRET_KEY, fournis par Railway à l'exécution.
CMD ["./start.sh"]
