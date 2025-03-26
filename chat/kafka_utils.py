# kafka_utils.py
import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)

# تكوين المنتج (Producer)
kafka_producer = KafkaProducer(
    bootstrap_servers=['192.168.117.128:9094'],  # استبدل بـ brokers الخاصة بك
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
    # تم إزالة enable_idempotence لأنه غير مدعوم في هذه النسخة
)

def send_message_to_kafka(message):
    """
    إرسال رسالة إلى Kafka.

    Args:
        message (dict): الرسالة المراد إرسالها.

    Returns:
        bool: True إذا تم إرسال الرسالة بنجاح، False خلاف ذلك.
    """
    try:
        # إنشاء مفتاح للرسالة - نستخدم معرف الرسالة أو مزيج من المرسل والمستقبل
        # المفتاح يساعد في ضمان أن الرسائل المتعلقة بنفس المحادثة تذهب إلى نفس القسم (partition)
        if 'message_id' in message:
            # استخدام معرف الرسالة كمفتاح إذا كان موجودًا
            key = str(message['message_id']).encode('utf-8')
        elif 'sender_id' in message and 'receiver_id' in message:
            # استخدام مزيج من معرفات المرسل والمستقبل كمفتاح
            key = f"{message['sender_id']}_{message['receiver_id']}".encode('utf-8')
        else:
            # استخدام الطابع الزمني كمفتاح إذا لم تتوفر المعرفات
            key = str(message.get('timestamp', '')).encode('utf-8')

        # إرسال الرسالة بشكل غير متزامن (Asynchronously) مع المفتاح
        future = kafka_producer.send('chat_messages', key=key, value=message)

        # انتظر حتى يتم إرسال الرسالة (يمكنك إزالة هذا إذا كنت لا تريد الانتظار)
        record_metadata = future.get(timeout=10)  # انتظر لمدة 10 ثوانٍ

        logger.info(f"تم إرسال الرسالة إلى topic:{record_metadata.topic}، partition:{record_metadata.partition}, offset:{record_metadata.offset}، key:{key}")
        return True

    except KafkaError as e:
        logger.error(f"فشل إرسال الرسالة إلى Kafka: {e}")
        return False

    except Exception as e:
        logger.exception(f"خطأ غير متوقع أثناء إرسال الرسالة إلى Kafka: {e}")
        return False

def close_kafka_producer():
    """إغلاق المنتج (Producer) عند إيقاف التطبيق."""
    try:
        kafka_producer.close()
        logger.info("تم إغلاق منتج Kafka.")
    except Exception as e:
        logger.error(f"خطأ أثناء إغلاق منتج Kafka: {e}")