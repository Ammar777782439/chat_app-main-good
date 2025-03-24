"""
وحدة تكامل Kafka مع تطبيق الدردشة.

هذه الوحدة توفر فئات ودوال لإرسال واستقبال رسائل الدردشة من وإلى Kafka.
"""

import json
import logging
import threading
import time
from confluent_kafka import Producer, Consumer, KafkaError
from datetime import datetime

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaChatProducer:
    """
    منتج Kafka لإرسال رسائل الدردشة.
    """
    
    def __init__(self, bootstrap_servers=None):
        """
        تهيئة منتج Kafka.
        
        Args:
            bootstrap_servers (str, optional): قائمة خوادم Kafka مفصولة بفواصل.
                الافتراضي هو 'localhost:9093,localhost:9094'.
        """
        if bootstrap_servers is None:
            bootstrap_servers = 'localhost:9093,localhost:9094'
        
        # إعدادات المنتج
        self.config = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': 'chat-producer'
        }
        
        try:
            # إنشاء منتج Kafka
            self.producer = Producer(self.config)
            logger.info(f"تم تهيئة منتج Kafka بنجاح: {bootstrap_servers}")
        except Exception as e:
            logger.error(f"فشل تهيئة منتج Kafka: {str(e)}")
            self.producer = None
    
    def delivery_report(self, err, msg):
        """
        تقرير تسليم الرسائل.
        
        Args:
            err: كائن الخطأ أو None
            msg: كائن الرسالة
        """
        if err is not None:
            logger.error(f"فشل تسليم الرسالة: {err}")
        else:
            logger.info(f"تم تسليم الرسالة إلى {msg.topic()} [قسم {msg.partition()}] عند الموضع {msg.offset()}")
    
    def send_message(self, sender, receiver, message, message_id=None, action="create"):
        """
        إرسال رسالة دردشة إلى Kafka.
        
        Args:
            sender (str): اسم المستخدم المرسل
            receiver (str): اسم المستخدم المستقبل
            message (str): محتوى الرسالة
            message_id (int, optional): معرف الرسالة. مطلوب لعمليات التحديث والحذف.
            action (str, optional): الإجراء المراد تنفيذه. واحد من "create"، "update"، أو "delete".
                الافتراضي هو "create".
        
        Returns:
            bool: True إذا تم إرسال الرسالة بنجاح، False خلاف ذلك.
        """
        if self.producer is None:
            logger.error("منتج Kafka غير مهيأ")
            return False
        
        try:
            # إنشاء بيانات الرسالة
            message_data = {
                "sender": sender,
                "receiver": receiver,
                "action": action,
                "timestamp": datetime.now().isoformat(),
            }
            
            # إضافة البيانات المناسبة بناءً على نوع العملية
            if action == "create":
                message_data["content"] = message
            elif action == "update":
                message_data["content"] = message
                message_data["message_id"] = message_id
            elif action == "delete":
                message_data["message_id"] = message_id
            
            # اختيار الموضوع المناسب
            topic = f"chat_messages_{action}"
            
            # تحويل الرسالة إلى JSON
            message_json = json.dumps(message_data)
            
            # إرسال الرسالة إلى Kafka
            self.producer.produce(
                topic=topic,
                key=f"{sender}_{receiver}".encode('utf-8') if sender and receiver else None,
                value=message_json.encode('utf-8'),
                callback=self.delivery_report
            )
            
            # تنفيذ الإرسال
            self.producer.poll(0)
            
            logger.info(f"تم إرسال رسالة إلى {topic}: {message_data}")
            return True
        except Exception as e:
            logger.error(f"فشل إرسال رسالة إلى Kafka: {str(e)}")
            return False
    
    def flush(self, timeout=10):
        """
        انتظار إرسال جميع الرسائل.
        
        Args:
            timeout (int, optional): الحد الأقصى للانتظار بالثواني. الافتراضي هو 10.
        """
        if self.producer is not None:
            self.producer.flush(timeout)
    
    def close(self):
        """
        إغلاق منتج Kafka.
        """
        if self.producer is not None:
            self.producer.flush()
            logger.info("تم إغلاق منتج Kafka")


class KafkaChatConsumer:
    """
    مستهلك Kafka لاستقبال رسائل الدردشة.
    """
    
    def __init__(self, bootstrap_servers=None, group_id=None, topics=None, message_handler=None):
        """
        تهيئة مستهلك Kafka.
        
        Args:
            bootstrap_servers (str, optional): قائمة خوادم Kafka مفصولة بفواصل.
                الافتراضي هو 'localhost:9093,localhost:9094'.
            group_id (str, optional): معرف مجموعة المستهلكين.
                الافتراضي هو 'chat-consumer'.
            topics (list, optional): قائمة المواضيع للاشتراك فيها.
                الافتراضي هو ['chat_messages_create', 'chat_messages_update', 'chat_messages_delete'].
            message_handler (callable, optional): دالة لمعالجة الرسائل المستلمة.
                يجب أن تقبل الدالة وسيطين: موضوع الرسالة وبيانات الرسالة.
        """
        if bootstrap_servers is None:
            bootstrap_servers = 'localhost:9093,localhost:9094'
        
        if group_id is None:
            group_id = 'chat-consumer'
        
        if topics is None:
            topics = ['chat_messages_create', 'chat_messages_update', 'chat_messages_delete']
        
        # إعدادات المستهلك
        self.config = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True,
            'auto.commit.interval.ms': 1000,
            'session.timeout.ms': 10000,
            'max.poll.interval.ms': 300000,
            'heartbeat.interval.ms': 3000
        }
        
        self.topics = topics
        self.message_handler = message_handler
        self.running = False
        self.consumer = None
        self.consumer_thread = None
    
    def start(self):
        """
        بدء استهلاك الرسائل من Kafka.
        
        Returns:
            bool: True إذا تم بدء المستهلك بنجاح، False خلاف ذلك.
        """
        if self.running:
            logger.warning("مستهلك Kafka قيد التشغيل بالفعل")
            return False
        
        try:
            # إنشاء مستهلك Kafka
            self.consumer = Consumer(self.config)
            
            # الاشتراك في المواضيع
            self.consumer.subscribe(self.topics)
            
            logger.info(f"تم تهيئة مستهلك Kafka بنجاح: {self.config['bootstrap.servers']}")
            logger.info(f"تم الاشتراك في المواضيع: {self.topics}")
            
            # بدء خيط الاستهلاك
            self.running = True
            self.consumer_thread = threading.Thread(target=self._consume_loop)
            self.consumer_thread.daemon = True
            self.consumer_thread.start()
            
            return True
        except Exception as e:
            logger.error(f"فشل بدء مستهلك Kafka: {str(e)}")
            return False
    
    def _consume_loop(self):
        """
        حلقة استهلاك الرسائل من Kafka.
        """
        try:
            while self.running:
                # محاولة قراءة رسالة
                msg = self.consumer.poll(1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"وصلنا إلى نهاية القسم {msg.partition()}")
                    else:
                        logger.error(f"خطأ في استهلاك الرسائل: {msg.error()}")
                    continue
                
                # معالجة الرسالة
                try:
                    # قراءة قيمة الرسالة
                    message_value = msg.value().decode('utf-8')
                    
                    # تحويل الرسالة من JSON
                    message_data = json.loads(message_value)
                    
                    # استدعاء معالج الرسائل إذا كان موجودًا
                    if self.message_handler:
                        self.message_handler(msg.topic(), message_data)
                    else:
                        logger.info(f"استلام رسالة من {msg.topic()}: {message_data}")
                except Exception as e:
                    logger.error(f"خطأ في معالجة الرسالة: {str(e)}")
        except Exception as e:
            logger.error(f"خطأ في حلقة الاستهلاك: {str(e)}")
        finally:
            if self.consumer:
                self.consumer.close()
                logger.info("تم إغلاق مستهلك Kafka")
    
    def stop(self):
        """
        إيقاف استهلاك الرسائل من Kafka.
        """
        if not self.running:
            logger.warning("مستهلك Kafka ليس قيد التشغيل")
            return
        
        self.running = False
        
        if self.consumer_thread:
            self.consumer_thread.join(timeout=10)
        
        if self.consumer:
            self.consumer.close()
            self.consumer = None
        
        logger.info("تم إيقاف مستهلك Kafka")


# مثال على استخدام المنتج والمستهلك
def example_message_handler(topic, message_data):
    """
    مثال على معالج الرسائل.
    
    Args:
        topic (str): موضوع الرسالة
        message_data (dict): بيانات الرسالة
    """
    action = message_data.get('action')
    sender = message_data.get('sender')
    receiver = message_data.get('receiver')
    
    if action == 'create':
        content = message_data.get('content')
        print(f"رسالة جديدة من {sender} إلى {receiver}: {content}")
    elif action == 'update':
        content = message_data.get('content')
        message_id = message_data.get('message_id')
        print(f"تحديث الرسالة {message_id} من {sender} إلى {receiver}: {content}")
    elif action == 'delete':
        message_id = message_data.get('message_id')
        print(f"حذف الرسالة {message_id} من {sender} إلى {receiver}")


def example_usage():
    """
    مثال على استخدام المنتج والمستهلك.
    """
    # إنشاء مستهلك Kafka
    consumer = KafkaChatConsumer(message_handler=example_message_handler)
    consumer.start()
    
    # إنشاء منتج Kafka
    producer = KafkaChatProducer()
    
    try:
        # إرسال رسالة جديدة
        producer.send_message(
            sender="user1",
            receiver="user2",
            message="مرحبًا، هذه رسالة اختبار!",
            action="create"
        )
        
        # انتظار قليلاً
        time.sleep(2)
        
        # تحديث الرسالة
        producer.send_message(
            sender="user1",
            receiver="user2",
            message="مرحبًا، هذه رسالة اختبار معدلة!",
            message_id=1,
            action="update"
        )
        
        # انتظار قليلاً
        time.sleep(2)
        
        # حذف الرسالة
        producer.send_message(
            sender="user1",
            receiver="user2",
            message=None,
            message_id=1,
            action="delete"
        )
        
        # انتظار قليلاً لاستلام جميع الرسائل
        time.sleep(5)
    finally:
        # إغلاق المنتج والمستهلك
        producer.close()
        consumer.stop()


if __name__ == "__main__":
    example_usage()
