"""
Kafka utilities for the chat application.

This module provides utilities for interacting with Kafka, including a producer
for sending messages to Kafka topics. It handles the configuration and connection
to Kafka brokers.
"""

import json
import logging
from kafka import KafkaProducer
from django.conf import settings
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

class ChatKafkaProducer:
    """
    Kafka producer for chat messages.

    This class provides methods for sending chat messages to Kafka topics.
    It handles the serialization of messages to JSON and manages the connection
    to Kafka brokers.
    """

    def __init__(self, bootstrap_servers=None, topic=None):
        """
        Initialize the Kafka producer.

        Args:
            bootstrap_servers: Kafka broker addresses (default: from settings.KAFKA_CONFIG)
            topic: The Kafka topic to send messages to (default: from settings.KAFKA_CONFIG)
        """
        # Use settings from Django settings if not provided
        kafka_config = getattr(settings, 'KAFKA_CONFIG', {})
        self.bootstrap_servers = bootstrap_servers or kafka_config.get('bootstrap_servers', '192.168.117.128:9094')
        self.topic = topic or kafka_config.get('topic', 'chat_messages')

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                # Additional configuration for reliability
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,   # Retry sending on failure
                max_in_flight_requests_per_connection=1  # Ensure ordering
            )
            logger.info(f"Kafka producer initialized with bootstrap servers: {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {str(e)}")
            self.producer = None

    def send_message(self, message_data, key=None):
        """
        Send a message to the Kafka topic.

        Args:
            message_data: Dictionary containing message data
            key: Optional message key for partitioning (default: None)

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False

        try:
            future = self.producer.send(self.topic, value=message_data, key=key)
            # Wait for the message to be sent
            future.get(timeout=10)
            logger.info(f"Message sent to Kafka topic {self.topic}: {message_data}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {str(e)}")
            return False

    async def send_message_async(self, message_data, key=None):
        """
        Send a message to Kafka asynchronously.

        This method wraps the synchronous send_message method to be used in async contexts.

        Args:
            message_data: Dictionary containing message data
            key: Optional message key for partitioning (default: None)

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        return await sync_to_async(self.send_message)(message_data, key)

    def close(self):
        """
        Close the Kafka producer.
        """
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")

# Create a singleton instance of the producer
# This will be initialized when the module is imported
kafka_producer = ChatKafkaProducer()
