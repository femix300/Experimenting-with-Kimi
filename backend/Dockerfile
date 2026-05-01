FROM python:3.10-slim

WORKDIR /app

# System deps (rarely changes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps FIRST (cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code LAST (tiny layer, fast push)
COPY . .

RUN python manage.py collectstatic --noinput 2>/dev/null || true

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--timeout", "120"]
