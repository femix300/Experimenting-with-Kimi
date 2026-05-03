FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput 2>/dev/null || true

# Bake migrations into image so auth_user table always exists on Cloud Run
RUN SECRET_KEY=dummy-build-time-key BAYSE_API_BASE_URL=https://relay.bayse.markets FIREBASE_CREDENTIALS_PATH=/tmp/dummy.json GEMINI_API_KEY=dummy BAYSE_PUBLIC_KEY=dummy BAYSE_SECRET_KEY=dummy python manage.py migrate --run-syncdb

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--timeout", "120"]
