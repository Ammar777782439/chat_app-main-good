from confluent_kafka import Producer
import json
import time
import sys

def delivery_report(err, msg):
    """
    تقرير تسليم الرسائل
    """
    if err is not None:
        print(f"فشل تسليم الرسالة: {err}")
    else:
        print(f"تم تسليم الرسالة إلى {msg.topic()} [قسم {msg.partition()}] عند الموضع {msg.offset()}")

def test_producer():
    # إعدادات المنتج
    config = {
        'bootstrap.servers': '192.168.117.128:9093',  # يمكنك تغييره إلى localhost:9094 لاختبار الوسيط الآخر
        'client.id': 'python-test-producer',
        # إضافة إعدادات إضافية لتجنب مشكلة حل أسماء المضيفين
        'broker.address.family': 'v4',  # استخدام IPv4 فقط
        'debug': 'broker,topic,metadata'  # إضافة معلومات تشخيصية
    }

    print(f"\nاختبار الاتصال بـ Kafka على {config['bootstrap.servers']}...")

    # إنشاء منتج Kafka
    producer = Producer(config)

    # اسم الموضوع
    topic = 'test_topic'

    # إرسال 5 رسائل اختبار
    for i in range(5):
        # إنشاء رسالة اختبار
        message = {
            'id': i,
            'message': f'رسالة اختبار رقم {i}',
            'timestamp': time.time()
        }

        # تحويل الرسالة إلى JSON
        message_json = json.dumps(message)

        # طباعة الرسالة التي سيتم إرسالها
        print(f"إرسال: {message_json}")

        # إرسال الرسالة إلى Kafka
        producer.produce(
            topic=topic,
            key=str(i),
            value=message_json,
            callback=delivery_report
        )

        # تنفيذ الإرسال
        producer.poll(0)

        # انتظار قليلاً بين الرسائل
        time.sleep(1)

    # انتظار إرسال جميع الرسائل
    producer.flush()
    print("تم إرسال جميع الرسائل بنجاح")

if __name__ == "__main__":
    test_producer()
