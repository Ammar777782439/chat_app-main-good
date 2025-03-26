"""
Signals for the chat application.

This module contains signal handlers that are triggered on chat model events.
It includes handlers for message creation, update, and deletion that send
the corresponding events to Kafka.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Message
from .kafka_utils import send_message_to_kafka

# Configure logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Message)
def message_saved_handler(sender, instance, created, **kwargs):
    """
    Handle the post_save signal for Message model.

    This signal is triggered after a message is saved. It sends the message
    data to Kafka, indicating whether it's a new message or an update.

    Args:
        sender: The model class that sent the signal (Message model)
        instance: The actual Message instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    try:
        # Prepare message data for Kafka
        message_data = {
            'event_type': 'message_created' if created else 'message_updated',
            'timestamp': timezone.now().isoformat(),
            'message_id': instance.id,
            'sender_id': instance.sender.id,
            'sender_username': instance.sender.username,
            'receiver_id': instance.receiver.id,
            'receiver_username': instance.receiver.username,
            'content': instance.content,
            'created_at': instance.timestamp.isoformat(),

        }

        # Add deleted_at if it exists
        if instance.deleted_at:
            message_data['deleted_at'] = instance.deleted_at.isoformat()

        # Send to Kafka
        success = send_message_to_kafka(message_data)
        if success:
            logger.info(f"{'New' if created else 'Updated'} message sent to Kafka: ID {instance.id}")
        else:
            logger.error(f"Failed to send {'new' if created else 'updated'} message to Kafka: ID {instance.id}")

    except Exception as e:
        logger.error(f"Error in message_saved_handler: {e}")

@receiver(post_delete, sender=Message)
def message_deleted_handler(sender, instance, **kwargs):
    """
    Handle the post_delete signal for Message model.

    This signal is triggered after a message is deleted. It sends the message
    deletion event to Kafka.

    Args:
        sender: The model class that sent the signal (Message model)
        instance: The actual Message instance being deleted
        **kwargs: Additional keyword arguments
    """
    try:
        # Prepare message deletion data for Kafka
        message_data = {
            'event_type': 'message_deleted',
            'timestamp': timezone.now().isoformat(),
            'message_id': instance.id,
            'sender_id': instance.sender.id,
            'sender_username': instance.sender.username,
            'receiver_id': instance.receiver.id,
            'receiver_username': instance.receiver.username,
        }

        # Send to Kafka
        success = send_message_to_kafka(message_data)
        if success:
            logger.info(f"Message deletion sent to Kafka: ID {instance.id}")
        else:
            logger.error(f"Failed to send message deletion to Kafka: ID {instance.id}")

    except Exception as e:
        logger.error(f"Error in message_deleted_handler: {e}")

# تم إزالة الدالة close غير الصحيحة