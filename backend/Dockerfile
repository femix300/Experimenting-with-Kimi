FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput 2>/dev/null || true

# Run migrate with error tolerance, then start gunicorn
CMD sh -c "python manage.py migrate --run-syncdb 2>/dev/null || true && gunicorn config.wsgi:application --bind 0.0.0.0:8080 --workers 2 --threads 4 --timeout 120"
