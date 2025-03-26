"""
مستهلكي WebSocket مع دعم Kafka لتطبيق الدردشة.

هذا الوحدة تحتوي على فئة ChatConsumerWithKafka التي تمتد من ChatConsumer
وتضيف دعم إرسال رسائل الدردشة إلى Kafka.
"""

import json
import logging
from django.conf import settings
from .consumers import ChatConsumer
from .agents.kafka_chat_agent import KafkaChatAgent

# إعداد التسجيل
logger = logging.getLogger(__name__)

class ChatConsumerWithKafka(ChatConsumer):
    """
    مستهلك WebSocket مع دعم Kafka لتطبيق الدردشة.
    
    هذه الفئة تمتد من ChatConsumer وتضيف دعم إرسال رسائل الدردشة إلى Kafka.
    وهي تحافظ على جميع وظائف ChatConsumer الأصلي مع إضافة وظائف Kafka.
    """
    
    async def connect(self):
        """
        التعامل مع اتصال WebSocket.
        
        تمتد هذه الطريقة من ChatConsumer.connect وتضيف تهيئة وكيل Kafka.
        """
        # تهيئة وكيل Kafka
        self.kafka_agent = KafkaChatAgent.get_instance()
        
        # إرسال حدث تسجيل الدخول إلى Kafka (اختياري)
        if getattr(settings, 'KAFKA_ENABLED', False):
            try:
                # استدعاء طريقة الاتصال الأصلية أولاً لتهيئة self.room_name
                await super().connect()
                
                # إرسال حدث تسجيل الدخول إلى Kafka
                await self.kafka_agent.send_chat_message(
                    sender_id=self.scope['user'].id,
                    receiver_id=self.room_name,
                    content="",  # رسالة فارغة لأنها مجرد حدث تسجيل دخول
                    metadata={
                        "event_type": "login",
                        "room_name": self.room_name
                    }
                )
                
                logger.info(f"تم إرسال حدث تسجيل الدخول إلى Kafka: {self.scope['user'].username} -> {self.room_name}")
            except Exception as e:
                logger.error(f"فشل إرسال حدث تسجيل الدخول إلى Kafka: {str(e)}")
                # استمر حتى لو فشل إرسال الحدث إلى Kafka
                if not hasattr(self, 'room_name'):
                    await super().connect()
        else:
            # إذا كان Kafka غير ممكّن، استدعاء طريقة الاتصال الأصلية فقط
            await super().connect()
    
    async def receive(self, text_data):
        """
        التعامل مع استقبال رسائل من WebSocket.
        
        تمتد هذه الطريقة من ChatConsumer.receive وتضيف إرسال الرسائل إلى Kafka.
        """
        # تحليل البيانات المستلمة
        text_data_json = json.loads(text_data)
        
        # التحقق من نوع العملية (إرسال، تحديث، أو حذف)
        message_id = text_data_json.get('message_id', None)
        delete_message_id = text_data_json.get('delete_message_id', None)
        
        # إرسال الرسالة إلى Kafka إذا كان ممكّنًا
        if getattr(settings, 'KAFKA_ENABLED', False) and hasattr(self, 'kafka_agent'):
            try:
                # حالة حذف رسالة
                if delete_message_id:
                    await self.kafka_agent.send_message(
                        message_data={
                            'message_id': delete_message_id,
                            'sender_id': self.scope['user'].id,
                            'receiver_id': self.room_name,
                            'action': 'delete',
                            'timestamp': text_data_json.get('timestamp', None)
                        }
                    )
                    logger.info(f"تم إرسال حدث حذف الرسالة إلى Kafka: {delete_message_id}")
                
                # حالة تحديث رسالة
                elif message_id:
                    await self.kafka_agent.send_chat_message(
                        sender_id=self.scope['user'].id,
                        receiver_id=self.room_name,
                        content=text_data_json.get('message', ''),
                        message_id=message_id,
                        metadata={
                            'action': 'update',
                            'timestamp': text_data_json.get('timestamp', None)
                        }
                    )
                    logger.info(f"تم إرسال حدث تحديث الرسالة إلى Kafka: {message_id}")
                
                # حالة إرسال رسالة جديدة
                elif 'message' in text_data_json:
                    await self.kafka_agent.send_chat_message(
                        sender_id=self.scope['user'].id,
                        receiver_id=self.room_name,
                        content=text_data_json['message'],
                        metadata={
                            'action': 'create',
                            'timestamp': text_data_json.get('timestamp', None)
                        }
                    )
                    logger.info(f"تم إرسال رسالة جديدة إلى Kafka: {self.scope['user'].username} -> {self.room_name}")
            
            except Exception as e:
                logger.error(f"فشل إرسال الرسالة إلى Kafka: {str(e)}")
                # استمر حتى لو فشل إرسال الرسالة إلى Kafka
        
        # استدعاء طريقة الاستقبال الأصلية لمعالجة الرسالة كالمعتاد
        await super().receive(text_data)
    
    async def disconnect(self, close_code):
        """
        التعامل مع قطع اتصال WebSocket.
        
        تمتد هذه الطريقة من ChatConsumer.disconnect وتضيف تنظيف موارد Kafka.
        """
        # إرسال حدث تسجيل الخروج إلى Kafka (اختياري)
        if getattr(settings, 'KAFKA_ENABLED', False) and hasattr(self, 'kafka_agent') and hasattr(self, 'room_name'):
            try:
                await self.kafka_agent.send_chat_message(
                    sender_id=self.scope['user'].id,
                    receiver_id=self.room_name,
                    content="",  # رسالة فارغة لأنها مجرد حدث تسجيل خروج
                    metadata={
                        "event_type": "logout",
                        "room_name": self.room_name,
                        "close_code": close_code
                    }
                )
                logger.info(f"تم إرسال حدث تسجيل الخروج إلى Kafka: {self.scope['user'].username} -> {self.room_name}")
            except Exception as e:
                logger.error(f"فشل إرسال حدث تسجيل الخروج إلى Kafka: {str(e)}")
        
        # تنظيف موارد Kafka
        if hasattr(self, 'kafka_agent'):
            try:
                self.kafka_agent.flush()
                logger.debug("تم تنظيف موارد Kafka")
            except Exception as e:
                logger.error(f"فشل تنظيف موارد Kafka: {str(e)}")
        
        # استدعاء طريقة قطع الاتصال الأصلية
        await super().disconnect(close_code)
