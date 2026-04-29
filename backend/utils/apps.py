"""
Django AppConfig for Firebase initialization.

Place this in an existing app's apps.py (e.g., backend/utils/apps.py)
and add the corresponding entry to INSTALLED_APPS.

Alternatively, add the ready() method to any existing AppConfig
(e.g., signals.apps.SignalsConfig or portfolio.apps.PortfolioConfig).
"""

from django.apps import AppConfig


class FirestoreConfig(AppConfig):
    """
    Dedicated Django app that initializes Firebase on startup.

    Installation:
        1. Place this file at: utils/apps.py  (next to firebase_client.py)
        2. Create utils/__init__.py if it doesn't exist.
        3. In settings.py INSTALLED_APPS, add:
               'utils.apps.FirestoreConfig',
           Place it FIRST in the list so Firebase is ready before other apps.
    """
    name = "utils"
    verbose_name = "Firestore Client"

    def ready(self):
        # Avoid initializing during management commands that don't need it
        import sys
        if "runserver" not in sys.argv and "gunicorn" not in sys.argv[0]:
            # Still initialize for Celery, but skip for makemigrations/migrate/etc.
            if "celery" not in sys.argv[0]:
                return

        from utils.firebase_client import get_firestore_client
        client = get_firestore_client()
        if client:
            import logging
            logging.getLogger(__name__).info("Firestore client ready.")
        else:
            import logging
            logging.getLogger(__name__).warning(
                "Firestore client NOT initialized. Check credentials."
            )


# ---------------------------------------------------------------------------
# Alternative: Inline in existing AppConfig
# ---------------------------------------------------------------------------
# If you don't want a new app, add this ready() method to any existing apps.py:
#
#   class SignalsConfig(AppConfig):
#       name = 'signals'
#
#       def ready(self):
#           from utils.firebase_client import get_firestore_client
#           get_firestore_client()
#
# Same for portfolio/apps.py or markets/apps.py.
# ---------------------------------------------------------------------------