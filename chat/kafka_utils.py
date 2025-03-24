"""
Kafka utilities for the chat application.

This module provides utility functions for interacting with Kafka,
including producers and consumers for sending and receiving messages.
"""

import json
from kafka import KafkaProducer, KafkaConsumer
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# تكوين منتج Kafka
def get_kafka_producer():
    """
    Create and return a Kafka producer instance.
    
    Returns:
        KafkaProducer: A configured Kafka producer instance.
    """
    try:
        # إنشاء منتج Kafka مع تكوين مناسب
        producer = KafkaProducer(
            bootstrap_servers=['kafka1:9092'],  # عنوان خادم Kafka
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),  # تحويل القيم إلى JSON
            acks='all'  # انتظار تأكيد من جميع النسخ المتماثلة
        )
        return producer
    except Exception as e:
        logger.error(f"Error creating Kafka producer: {e}")
        return None

# تكوين مستهلك Kafka
def get_kafka_consumer(topic, group_id=None):
    """
    Create and return a Kafka consumer instance.
    
    Args:
        topic (str): The Kafka topic to consume messages from.
        group_id (str, optional): Consumer group ID. Defaults to None.
        
    Returns:
        KafkaConsumer: A configured Kafka consumer instance.
    """
    try:
        # إنشاء مستهلك Kafka مع تكوين مناسب
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=['kafka1:9092'],  # عنوان خادم Kafka
            auto_offset_reset='earliest',  # بدء القراءة من أقدم الرسائل غير المقروءة
            enable_auto_commit=True,  # تأكيد تلقائي للرسائل المقروءة
            group_id=group_id,  # معرف المجموعة (اختياري)
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))  # تحويل القيم من JSON
        )
        return consumer
    except Exception as e:
        logger.error(f"Error creating Kafka consumer: {e}")
        return None

# إرسال رسالة إلى Kafka
def send_message_to_kafka(topic, message_data):
    """
    Send a message to a Kafka topic.
    
    Args:
        topic (str): The Kafka topic to send the message to.
        message_data (dict): The message data to send.
        
    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    producer = get_kafka_producer()
    if not producer:
        return False
    
    try:
        # إرسال الرسالة إلى الموضوع المحدد
        future = producer.send(topic, value=message_data)
        # انتظار تأكيد الإرسال
        record_metadata = future.get(timeout=10)
        logger.info(f"Message sent to {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")
        return True
    except Exception as e:
        logger.error(f"Error sending message to Kafka: {e}")
        return False
    finally:
        # إغلاق المنتج بعد الانتهاء
        producer.close()

# مثال على استخدام مستهلك Kafka في حلقة
def consume_messages_example(topic, group_id=None):
    """
    Example function to consume messages from a Kafka topic.
    
    Args:
        topic (str): The Kafka topic to consume messages from.
        group_id (str, optional): Consumer group ID. Defaults to None.
    """
    consumer = get_kafka_consumer(topic, group_id)
    if not consumer:
        return
    
    try:
        # استهلاك الرسائل في حلقة لا نهائية
        for message in consumer:
            logger.info(f"Received message: {message.value}")
            # هنا يمكنك معالجة الرسالة كما تريد
            process_message(message.value)
    except Exception as e:
        logger.error(f"Error consuming messages from Kafka: {e}")
    finally:
        # إغلاق المستهلك بعد الانتهاء
        consumer.close()

def process_message(message_data):
    """
    Process a message received from Kafka.
    
    Args:
        message_data (dict): The message data to process.
    """
    # هنا يمكنك إضافة المنطق الخاص بمعالجة الرسائل
    # على سبيل المثال، يمكنك حفظ الرسالة في قاعدة البيانات
    logger.info(f"Processing message: {message_data}")
