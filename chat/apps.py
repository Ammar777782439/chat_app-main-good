"""Django app configuration for the chat application.

This module defines the configuration for the chat application,
including any initialization code that should run when the app is loaded."""

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class ChatConfig(AppConfig):
    """Configuration for the chat application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        """
        Initialize the application.

        This method is called when the application is ready. It's a good place
        to initialize Kafka consumers and other background processes.
        """
        # تجنب تشغيل الكود مرتين في حالة استخدام Django development server
        import os
        if os.environ.get('RUN_MAIN', None) != 'true':
            return

        # بدء مستهلكي Kafka
        try:
            # استيراد وظيفة بدء مستهلكي Kafka
            from .kafka_integration_example import start_kafka_consumers

            # بدء المستهلكين
            kafka_threads = start_kafka_consumers()
            logger.info("Started Kafka consumers for chat application")
        except Exception as e:
            logger.error(f"Failed to start Kafka consumers: {e}")
