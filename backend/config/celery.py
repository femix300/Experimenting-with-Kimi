"""
Celery configuration for background tasks
"""
import os
from celery import Celery

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('edgeiq')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'background-signal-scanner': {
        'task': 'signals.tasks.background_signal_scanner',
        'schedule': 300.0,  # Every 5 minutes
        'options': {'queue': 'default'},
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
