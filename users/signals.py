"""
Signals for the users app.

This module contains signals that are triggered on user model events.
Currently, it includes:
- Creating an authentication token when a new user is created
"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """
    Create an authentication token for newly created users.
    
    This signal is triggered after a user is saved. If the user was just created
    (not updated), a new token is created for that user.
    
    Args:
        sender: The model class that sent the signal (User model)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        Token.objects.create(user=instance)
