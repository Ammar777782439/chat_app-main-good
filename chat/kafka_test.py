"""
Test script for Kafka integration.

This script provides simple tests to verify that Kafka is working correctly
with the chat application.
"""

import os
import sys
import django
import time
import json
from datetime import datetime

# إعداد بيئة Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_app.settings')
django.setup()

from django.contrib.auth.models import User
from chat.models import Message
from chat.kafka_utils import get_kafka_producer, get_kafka_consumer, send_message_to_kafka

def test_kafka_producer():
    """Test sending a message to Kafka."""
    print("Testing Kafka producer...")
    
    # إنشاء رسالة اختبار
    test_message = {
        'type': 'test',
        'message': 'Hello Kafka!',
        'timestamp': datetime.now().isoformat()
    }
    
    # إرسال الرسالة إلى Kafka
    success = send_message_to_kafka('test_topic', test_message)
    
    if success:
        print("✅ Successfully sent message to Kafka")
    else:
        print("❌ Failed to send message to Kafka")
    
    return success

def test_kafka_consumer():
    """Test receiving a message from Kafka."""
    print("Testing Kafka consumer...")
    print("Waiting for messages on 'test_topic'...")
    
    # إنشاء مستهلك Kafka
    consumer = get_kafka_consumer('test_topic', group_id='test_group')
    
    if not consumer:
        print("❌ Failed to create Kafka consumer")
        return False
    
    # تعيين مهلة للاستماع
    timeout = time.time() + 10  # 10 ثوانٍ
    
    # الاستماع للرسائل
    for message in consumer:
        print(f"✅ Received message: {message.value}")
        consumer.close()
        return True
        
        # التحقق من انتهاء المهلة
        if time.time() > timeout:
            print("❌ Timed out waiting for messages")
            consumer.close()
            return False

def run_tests():
    """Run all Kafka tests."""
    print("=== Starting Kafka Integration Tests ===")
    
    # اختبار المنتج
    producer_success = test_kafka_producer()
    
    # اختبار المستهلك (فقط إذا نجح اختبار المنتج)
    if producer_success:
        consumer_success = test_kafka_consumer()
    else:
        consumer_success = False
    
    # طباعة النتائج النهائية
    print("\n=== Kafka Integration Test Results ===")
    print(f"Producer Test: {'✅ Passed' if producer_success else '❌ Failed'}")
    print(f"Consumer Test: {'✅ Passed' if consumer_success else '❌ Failed'}")
    
    if producer_success and consumer_success:
        print("\n🎉 All tests passed! Kafka is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check your Kafka configuration.")

if __name__ == "__main__":
    run_tests()
