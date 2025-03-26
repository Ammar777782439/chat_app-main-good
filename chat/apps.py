from django.apps import AppConfig
import atexit


class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        """Import signals when Django starts and register shutdown handler."""
        import chat.signals  # noqa

        # Register shutdown handler to close Kafka producer
        from chat.kafka_utils import close_kafka_producer
        atexit.register(close_kafka_producer)
