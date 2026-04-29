"""
Celery tasks for portfolio operations
"""
from celery import shared_task
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


@shared_task
def async_calculate_portfolio_analytics(user_id=None):
    """
    Calculate portfolio analytics in background
    """
    from .analytics import calculate_portfolio_metrics
    
    if user_id:
        user = User.objects.get(id=user_id)
    else:
        user, _ = User.objects.get_or_create(username='default_user')
    
    metrics = calculate_portfolio_metrics(user)
    logger.info(f"Portfolio analytics calculated for {user.username}")
    return metrics
