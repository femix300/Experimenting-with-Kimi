from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import sync_profile_to_firestore


@receiver(post_save, sender=User)
def user_post_save(sender, instance, **kwargs):
    """Ensure user is synced to Firestore after save"""
    sync_profile_to_firestore(instance)
