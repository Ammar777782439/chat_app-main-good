"""
وكيل Kafka لإنتاج رسائل الدردشة.

هذا الوحدة تحتوي على وكيل KafkaChatAgent الذي يتعامل مع إنتاج رسائل الدردشة إلى Kafka.
الوكيل يستخدم نمط التصميم Singleton لضمان وجود نسخة واحدة فقط من المنتج.
"""

import json
import uuid
import logging
import threading
import time
import asyncio
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Optional, Callable, List, Union

from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError
from django.conf import settings

# إعداد التسجيل
logger = logging.getLogger(__name__)

def retry(exceptions, tries=4, delay=3, backoff=2, logger=None):
    """
    مزخرف لإعادة محاولة الوظيفة في حالة حدوث استثناء.

    Args:
        exceptions: الاستثناء أو قائمة الاستثناءات التي يجب إعادة المحاولة عند حدوثها.
        tries: عدد المحاولات الإجمالي.
        delay: التأخير الأولي بين المحاولات بالثواني.
        backoff: معامل التراجع (كل محاولة تنتظر هذا المعامل أكثر من المحاولة السابقة).
        logger: كائن التسجيل لتسجيل الأخطاء.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    msg = f"{str(e)}, إعادة المحاولة في {mdelay} ثواني..."
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator


class KafkaChatAgent:
    """
    وكيل Kafka لإنتاج رسائل الدردشة.

    هذا الوكيل مسؤول عن إنتاج رسائل الدردشة إلى Kafka. يستخدم نمط التصميم Singleton
    لضمان وجود نسخة واحدة فقط من المنتج في جميع أنحاء التطبيق.

    Attributes:
        _instance (KafkaChatAgent): النسخة الوحيدة من الوكيل.
        _lock (threading.Lock): قفل للتزامن عند إنشاء النسخة.
        producer (KafkaProducer): كائن منتج Kafka.
        config (dict): تكوين منتج Kafka.
        default_topic (str): الموضوع الافتراضي لإرسال الرسائل.
        retry_config (dict): تكوين إعادة المحاولة.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """
        إنشاء نسخة جديدة من الوكيل (أو إعادة النسخة الموجودة).

        Returns:
            KafkaChatAgent: النسخة الوحيدة من الوكيل.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(KafkaChatAgent, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, bootstrap_servers=None, client_id=None, default_topic=None,
                 retry_config=None, **kafka_config):
        """
        تهيئة وكيل Kafka.

        Args:
            bootstrap_servers (str or list, optional): قائمة خوادم Kafka.
                الافتراضي هو الإعداد من ملف الإعدادات أو ['localhost:9093', 'localhost:9094'].
            client_id (str, optional): معرف العميل للمنتج.
                الافتراضي هو 'chat-agent'.
            default_topic (str, optional): الموضوع الافتراضي لإرسال الرسائل.
                الافتراضي هو 'chat_messages'.
            retry_config (dict, optional): تكوين إعادة المحاولة.
                الافتراضي هو {'tries': 3, 'delay': 1, 'backoff': 2}.
            **kafka_config: إعدادات إضافية لمنتج Kafka.
        """
        # تجنب إعادة التهيئة
        if self._initialized:
            return

        # استخدام الإعدادات من ملف الإعدادات إذا كانت متوفرة
        if bootstrap_servers is None:
            bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS',
                                       ['localhost:9093', 'localhost:9094'])
            # تحويل السلسلة إلى قائمة إذا لزم الأمر
            if isinstance(bootstrap_servers, str):
                bootstrap_servers = bootstrap_servers.split(',')

        if client_id is None:
            client_id = getattr(settings, 'KAFKA_CLIENT_ID', 'chat-agent')

        if default_topic is None:
            default_topic = getattr(settings, 'KAFKA_CHAT_TOPIC', 'chat_messages')

        if retry_config is None:
            retry_config = {
                'tries': getattr(settings, 'KAFKA_RETRY_TRIES', 3),
                'delay': getattr(settings, 'KAFKA_RETRY_DELAY', 1),
                'backoff': getattr(settings, 'KAFKA_RETRY_BACKOFF', 2)
            }

        self.default_topic = default_topic
        self.retry_config = retry_config

        # إعدادات المنتج
        self.config = {
            'bootstrap_servers': bootstrap_servers,
            'client_id': client_id,
            'value_serializer': lambda x: json.dumps(x).encode('utf-8'),
            'key_serializer': lambda x: x.encode('utf-8') if x else None,
            'acks': 'all',  # انتظار تأكيد من جميع النسخ المتماثلة
            'retries': 3,   # عدد محاولات إعادة المحاولة
            'retry_backoff_ms': 500,  # وقت الانتظار بين المحاولات
            'request_timeout_ms': 30000,  # مهلة الطلب
            'api_version_auto_timeout_ms': 5000,  # مهلة اكتشاف إصدار API
            'connections_max_idle_ms': 10000,  # الحد الأقصى لوقت الخمول للاتصالات
            'reconnect_backoff_ms': 50,  # وقت الانتظار قبل إعادة الاتصال
            'reconnect_backoff_max_ms': 1000,  # الحد الأقصى لوقت الانتظار قبل إعادة الاتصال
        }

        # إضافة إعدادات إضافية
        self.config.update(kafka_config)

        # طباعة إعدادات الاتصال للتشخيص
        logger.info(f"محاولة الاتصال بـ Kafka: {bootstrap_servers}")

        try:
            # إنشاء منتج Kafka
            self.producer = KafkaProducer(**self.config)
            logger.info(f"تم تهيئة وكيل Kafka بنجاح: {bootstrap_servers}")
            self._initialized = True
        except Exception as e:
            logger.error(f"فشل تهيئة وكيل Kafka: {str(e)}")
            logger.warning("سيتم تجاهل عمليات إرسال الرسائل إلى Kafka")
            self.producer = None
            self._initialized = False

            # محاولة تشخيص المشكلة
            if 'NoBrokersAvailable' in str(e):
                logger.error("لا يمكن الاتصال بوسطاء Kafka. تأكد من أن Kafka يعمل وأن إعدادات الاتصال صحيحة.")
                logger.error(f"عناوين الوسطاء المستخدمة: {bootstrap_servers}")
                logger.error("جرب استخدام عنوان IP بدلاً من localhost، مثل: 192.168.117.128:9094")
            elif 'ConnectionError' in str(e):
                logger.error("خطأ في الاتصال بـ Kafka. تأكد من أن Kafka يعمل وأن الشبكة متاحة.")
            elif 'TimeoutError' in str(e):
                logger.error("انتهت مهلة الاتصال بـ Kafka. تأكد من أن Kafka يعمل وأن الشبكة سريعة بما فيه الكفاية.")

    def delivery_callback(self, err, msg):
        """
        دالة رد الاتصال للتسليم.

        Args:
            err: الخطأ (إذا حدث).
            msg: كائن الرسالة.
        """
        if err is not None:
            logger.error(f"فشل تسليم الرسالة: {err}")
        else:
            logger.debug(f"تم تسليم الرسالة إلى {msg.topic()} [قسم {msg.partition()}] عند الموضع {msg.offset()}")

    @retry((KafkaError, KafkaTimeoutError), logger=logger)
    def send_message(self, message_data: Dict[str, Any], topic: str = None, key: str = None) -> bool:
        """
        إرسال رسالة إلى Kafka.

        Args:
            message_data (dict): بيانات الرسالة للإرسال.
            topic (str, optional): الموضوع لإرسال الرسالة إليه.
                الافتراضي هو الموضوع الافتراضي.
            key (str, optional): مفتاح الرسالة (للتقسيم).
                الافتراضي هو معرف الرسالة.

        Returns:
            bool: True إذا تم إرسال الرسالة بنجاح، False خلاف ذلك.

        Raises:
            KafkaError: إذا فشل إرسال الرسالة بعد جميع محاولات إعادة المحاولة.
        """
        if self.producer is None:
            logger.error("لم يتم تهيئة منتج Kafka")
            return False

        if topic is None:
            topic = self.default_topic

        if key is None and 'message_id' in message_data:
            key = message_data['message_id']

        try:
            # إرسال الرسالة إلى Kafka
            future = self.producer.send(
                topic=topic,
                key=key,
                value=message_data
            )

            # انتظار التأكيد (اختياري، يمكن إزالته للأداء)
            try:
                record_metadata = future.get(timeout=5)  # تقليل المهلة لتجنب التأخير الطويل
                logger.info(f"تم إرسال الرسالة إلى {topic} [قسم {record_metadata.partition}] عند الموضع {record_metadata.offset}")
            except KafkaTimeoutError:
                logger.warning(f"انتهت مهلة انتظار تأكيد إرسال الرسالة إلى {topic}، لكن الرسالة قد تكون أرسلت بنجاح")

            return True

        except Exception as e:
            logger.error(f"خطأ في إرسال الرسالة إلى Kafka: {str(e)}")

            # تشخيص المشكلة
            if 'NoBrokersAvailable' in str(e):
                logger.error("لا يمكن الاتصال بوسطاء Kafka. تأكد من أن Kafka يعمل وأن إعدادات الاتصال صحيحة.")
            elif 'NotLeaderForPartition' in str(e):
                logger.error("الوسيط ليس قائدًا للقسم. قد تكون هناك مشكلة في تكوين Kafka.")
            elif 'TopicAuthorizationFailedException' in str(e):
                logger.error("فشل التفويض للموضوع. تأكد من أن لديك الصلاحيات المناسبة.")

            raise  # إعادة رفع الاستثناء للتعامل معه بواسطة مزخرف retry

    async def send_chat_message(self, sender_id: Union[int, str], receiver_id: Union[int, str],
                               content: str, message_id: str = None,
                               metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        إرسال رسالة دردشة إلى Kafka.

        Args:
            sender_id (int or str): معرف المرسل.
            receiver_id (int or str): معرف المستلم.
            content (str): محتوى الرسالة.
            message_id (str, optional): معرف الرسالة.
                الافتراضي هو معرف UUID جديد.
            metadata (dict, optional): بيانات وصفية إضافية للرسالة.

        Returns:
            dict: بيانات الرسالة التي تم إرسالها.
        """
        # إنشاء معرف رسالة جديد إذا لم يتم توفيره
        if message_id is None:
            message_id = str(uuid.uuid4())

        # إنشاء بيانات الرسالة
        message_data = {
            'message_id': message_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'type': 'chat_message'
        }

        # إضافة البيانات الوصفية إذا تم توفيرها
        if metadata:
            message_data.update(metadata)

        # التحقق من تهيئة المنتج
        if not self.producer:
            logger.warning(f"لم يتم تهيئة منتج Kafka. تجاهل إرسال الرسالة: {message_id}")
            return message_data

        # إرسال الرسالة إلى Kafka (في خيط منفصل لتجنب حظر الحلقة الحدثية)
        try:
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                lambda: self.send_message(message_data)
            )

            if not success:
                logger.warning(f"فشل إرسال رسالة الدردشة إلى Kafka: {message_id}")
        except Exception as e:
            logger.error(f"خطأ في إرسال رسالة الدردشة إلى Kafka: {message_id} - {str(e)}")

        return message_data

    async def process_websocket_message(self, text_data: str, user_id: Union[int, str],
                                       room_id: Union[int, str] = None) -> Dict[str, Any]:
        """
        معالجة رسالة WebSocket وإرسالها إلى Kafka.

        Args:
            text_data (str): بيانات النص المستلمة من WebSocket.
            user_id (int or str): معرف المستخدم المرسل.
            room_id (int or str, optional): معرف غرفة الدردشة.
                إذا لم يتم توفيره، سيتم استخراجه من بيانات النص.

        Returns:
            dict: بيانات الرسالة التي تم إرسالها.
        """
        try:
            # تحليل بيانات النص
            text_data_json = json.loads(text_data)

            # استخراج البيانات
            content = text_data_json.get('message')
            receiver_id = text_data_json.get('receiver_id', room_id)
            message_id = text_data_json.get('message_id', str(uuid.uuid4()))

            # التحقق من البيانات المطلوبة
            if not content:
                logger.error("محتوى الرسالة مفقود")
                return None

            if not receiver_id:
                logger.error("معرف المستلم مفقود")
                return None

            # استخراج البيانات الوصفية الإضافية
            metadata = {k: v for k, v in text_data_json.items()
                       if k not in ['message', 'receiver_id', 'message_id']}

            # إرسال الرسالة إلى Kafka
            return await self.send_chat_message(
                sender_id=user_id,
                receiver_id=receiver_id,
                content=content,
                message_id=message_id,
                metadata=metadata
            )

        except json.JSONDecodeError:
            logger.error(f"بيانات JSON غير صالحة: {text_data}")
            return None

        except Exception as e:
            logger.error(f"خطأ في معالجة رسالة WebSocket: {str(e)}")
            return None

    def flush(self, timeout: float = 10.0) -> None:
        """
        انتظار إرسال جميع الرسائل المعلقة.

        Args:
            timeout (float, optional): مهلة الانتظار بالثواني.
                الافتراضي هو 10 ثوانٍ.
        """
        if self.producer:
            self.producer.flush(timeout=timeout)

    def close(self) -> None:
        """
        إغلاق منتج Kafka.
        """
        if self.producer:
            self.producer.close()
            logger.info("تم إغلاق منتج Kafka")

    @classmethod
    def get_instance(cls, *args, **kwargs) -> 'KafkaChatAgent':
        """
        الحصول على النسخة الوحيدة من الوكيل.

        Returns:
            KafkaChatAgent: النسخة الوحيدة من الوكيل.
        """
        if cls._instance is None:
            return cls(*args, **kwargs)
        return cls._instance

    def __del__(self):
        """
        تنظيف الموارد عند حذف الكائن.
        """
        self.close()


# استخدام الوكيل في ChatConsumer

class ChatConsumerWithKafka:
    """
    مثال على كيفية استخدام KafkaChatAgent في ChatConsumer.

    هذا مثال فقط ويجب دمجه مع ChatConsumer الحالي.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # إنشاء وكيل Kafka
        self.kafka_agent = KafkaChatAgent.get_instance()

    async def receive(self, text_data):
        """
        استقبال رسالة من WebSocket وإرسالها إلى Kafka.
        """
        # معالجة الرسالة وإرسالها إلى Kafka
        message_data = await self.kafka_agent.process_websocket_message(
            text_data=text_data,
            user_id=self.scope['user'].id,
            room_id=self.room_name
        )

        if message_data:
            # إرسال الرسالة إلى المجموعة (لإرسالها إلى المستخدمين المتصلين)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_data['content'],
                    'sender_id': message_data['sender_id'],
                    'message_id': message_data['message_id'],
                    'timestamp': message_data['timestamp']
                }
            )

    def disconnect(self, close_code):
        """
        قطع اتصال WebSocket.
        """
        # تنظيف الموارد
        self.kafka_agent.flush()
        super().disconnect(close_code)


# مثال على كيفية دمج KafkaChatAgent مع ChatConsumer الحالي

"""
من chat.consumers import ChatConsumer
from chat.agents.kafka_chat_agent import KafkaChatAgent

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
"""
