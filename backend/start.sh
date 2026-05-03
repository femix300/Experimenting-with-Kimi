#!/bin/sh
# Wait for secrets to be available, then migrate and start gunicorn
sleep 2
python manage.py migrate --run-syncdb 2>&1
exec gunicorn config.wsgi:application --bind 0.0.0.0:8080 --workers 2 --threads 4 --timeout 120
