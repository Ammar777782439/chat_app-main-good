# وكلاء الدردشة (Chat Agents)

هذه الحزمة تحتوي على وكلاء مختلفين لتطبيق الدردشة. الوكلاء هم كائنات مستقلة تقوم بمهام محددة، مثل إنتاج رسائل الدردشة إلى Kafka أو معالجة الإشعارات.

## وكيل Kafka للدردشة (KafkaChatAgent)

وكيل `KafkaChatAgent` مسؤول عن إنتاج رسائل الدردشة إلى Kafka. يستخدم نمط التصميم Singleton لضمان وجود نسخة واحدة فقط من المنتج في جميع أنحاء التطبيق.

### الميزات الرئيسية

- **نمط Singleton**: ضمان وجود نسخة واحدة فقط من الوكيل.
- **إعادة المحاولة التلقائية**: إعادة محاولة إرسال الرسائل في حالة فشل الاتصال.
- **تسجيل الأحداث**: تسجيل جميع الأحداث والأخطاء.
- **تكوين مرن**: إمكانية تكوين الوكيل بطرق مختلفة.
- **إغلاق آمن**: تنظيف الموارد عند الإغلاق.
- **دعم async/await**: دعم البرمجة غير المتزامنة.

### مثال الاستخدام

```python
from chat.agents import KafkaChatAgent

# الحصول على نسخة من الوكيل
agent = KafkaChatAgent.get_instance()

# إرسال رسالة دردشة
await agent.send_chat_message(
    sender_id=1,
    receiver_id=2,
    content="مرحبًا!"
)

# معالجة رسالة WebSocket
message_data = await agent.process_websocket_message(
    text_data='{"message": "مرحبًا!", "receiver_id": 2}',
    user_id=1
)

# إغلاق الوكيل عند الانتهاء
agent.close()
```

### دمج الوكيل مع ChatConsumer

يمكن دمج الوكيل مع `ChatConsumer` الحالي كما يلي:

```python
from chat.consumers import ChatConsumer
from chat.agents import KafkaChatAgent

class ChatConsumerWithKafka(ChatConsumer):
    
    async def connect(self):
        # إنشاء وكيل Kafka
        self.kafka_agent = KafkaChatAgent.get_instance()
        # استدعاء طريقة الاتصال الأصلية
        await super().connect()
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        # معالجة الرسالة كالمعتاد
        # ...
        
        # إرسال الرسالة إلى Kafka
        await self.kafka_agent.send_chat_message(
            sender_id=self.scope['user'].id,
            receiver_id=self.room_name,  # أو معرف المستلم المناسب
            content=message
        )
        
        # استدعاء طريقة الاستقبال الأصلية
        await super().receive(text_data)
    
    async def disconnect(self, close_code):
        # تنظيف الموارد
        if hasattr(self, 'kafka_agent'):
            self.kafka_agent.flush()
        # استدعاء طريقة قطع الاتصال الأصلية
        await super().disconnect(close_code)
```

## إعدادات Kafka

يمكن تكوين إعدادات Kafka في ملف `settings.py`:

```python
# Kafka settings
KAFKA_ENABLED = True
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9093,localhost:9094'
KAFKA_CLIENT_ID = 'chat-agent'
KAFKA_CHAT_TOPIC = 'chat_messages'
KAFKA_RETRY_TRIES = 3
KAFKA_RETRY_DELAY = 1
KAFKA_RETRY_BACKOFF = 2
```
