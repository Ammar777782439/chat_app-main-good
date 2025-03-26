# chat/routing.py
from django.urls import re_path
from django.conf import settings
from . import consumers
from . import consumers_kafka

# استخدام ChatConsumerWithKafka إذا كان Kafka ممكّنًا، وإلا استخدام ChatConsumer العادي
if getattr(settings, 'KAFKA_ENABLED', False):
    websocket_urlpatterns = [
        re_path(r'ws/chat/(?P<room_name>[^/]+)/$', consumers_kafka.ChatConsumerWithKafka.as_asgi()),
    ]
    print("تم تمكين Kafka: استخدام ChatConsumerWithKafka")
else:
    websocket_urlpatterns = [
        re_path(r'ws/chat/(?P<room_name>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
    ]
    print("Kafka غير ممكّن: استخدام ChatConsumer العادي")
