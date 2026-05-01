"""Celery tasks for portfolio operations (Firestore-only)."""
from celery import shared_task
from utils.firebase_client import fs, Collection
import logging

logger = logging.getLogger(__name__)

@shared_task
def async_calculate_portfolio_analytics(user_id=None):
    """Calculate portfolio analytics in background."""
    from .analytics import calculate_portfolio_metrics

    # Look up user from Firestore instead of SQLite
    user_data = None
    if user_id:
        user_data = fs.get(Collection.USER_PROFILES, str(user_id))
    
    if not user_data:
        # Use a default anonymous profile
        user_data = {
            "id": "default_user",
            "username": "default_user",
            "bankroll": 10000,
        }

    metrics = calculate_portfolio_metrics(user_data)
    logger.info(f"Portfolio analytics calculated for {user_data.get('username', 'anonymous')}")
    return metrics
