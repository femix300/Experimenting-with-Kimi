"""
User Profile Model - Extends Django's User model
"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


class UserProfile(models.Model):
    """
    Extended user profile stored in SQLite (for auth) and synced to Firestore
    """
    RISK_CHOICES = [
        ('conservative', 'Conservative'),
        ('balanced', 'Balanced'),
        ('aggressive', 'Aggressive'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    risk_tolerance = models.CharField(max_length=20, choices=RISK_CHOICES, default='balanced')
    bankroll = models.DecimalField(max_digits=15, decimal_places=2, default=10000.00)
    total_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'users'
    
    def __str__(self):
        return f"{self.user.username}'s profile"
    
    @property
    def win_rate(self):
        if self.total_trades > 0:
            return (self.winning_trades / self.total_trades) * 100
        return 0


def sync_profile_to_firestore(user):
    """Sync user profile to Firestore"""
    try:
        from utils.firebase_client import fs, Collection
        
        profile_data = {
            "user_id": str(user.id),
            "username": user.username,
            "email": user.email or "",
            "risk_tolerance": user.profile.risk_tolerance,
            "bankroll": float(user.profile.bankroll),
            "total_pnl": float(user.profile.total_pnl),
            "total_trades": user.profile.total_trades,
            "winning_trades": user.profile.winning_trades,
            "created_at": user.profile.created_at.isoformat() if user.profile.created_at else None,
            "updated_at": user.profile.updated_at.isoformat() if user.profile.updated_at else None,
        }
        fs.set(Collection.USER_PROFILES, str(user.id), profile_data, merge=True)
        logger.info(f"Synced user {user.username} to Firestore")
    except Exception as e:
        logger.error(f"Failed to sync user to Firestore: {e}")


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when a new User is created"""
    if created:
        UserProfile.objects.create(user=instance)
        sync_profile_to_firestore(instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile and sync to Firestore"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
        sync_profile_to_firestore(instance)
