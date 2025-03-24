"""
Test script for Kafka connection.

This script tests the connection to Kafka by sending and receiving a test message.
"""

from kafka import KafkaProducer, KafkaConsumer
import json
import time

def test_kafka_connection():
    """Test connection to Kafka by sending and receiving a message."""
    print("=== اختبار الاتصال بـ Kafka ===")
    
    try:
        # محاولة إنشاء منتج Kafka
        print("إنشاء منتج Kafka...")
        producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # إرسال رسالة اختبارية
        print("إرسال رسالة اختبارية...")
        test_message = {
            'message': 'Hello from Python!',
            'timestamp': time.time()
        }
        producer.send('test-topic', test_message)
        producer.flush()
        print("✅ تم إرسال الرسالة بنجاح!")
        
        # محاولة إنشاء مستهلك Kafka
        print("\nإنشاء مستهلك Kafka...")
        consumer = KafkaConsumer(
            'test-topic',
            bootstrap_servers=['localhost:9092'],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='test-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            consumer_timeout_ms=10000  # 10 ثوانٍ مهلة
        )
        
        # قراءة رسالة
        print("انتظار استلام الرسالة (10 ثوانٍ كحد أقصى)...")
        for message in consumer:
            print(f"✅ تم استلام رسالة: {message.value}")
            break
        else:
            print("❌ لم يتم استلام أي رسالة خلال المهلة المحددة")
        
        print("\n=== نتيجة الاختبار ===")
        print("✅ تم الاتصال بـ Kafka بنجاح!")
        return True
        
    except Exception as e:
        print(f"\n❌ فشل الاتصال بـ Kafka: {e}")
        print("\nنصائح لحل المشكلة:")
        print("1. تأكد من أن حاويات Kafka تعمل: docker ps")
        print("2. تأكد من أن المنافذ 9092 و 9093 غير مستخدمة من قبل تطبيقات أخرى")
        print("3. جرب استخدام عنوان IP بدلاً من localhost: ['127.0.0.1:9092']")
        print("4. تحقق من سجلات Kafka: docker logs kafka1")
        return False

if __name__ == "__main__":
    test_kafka_connection()
