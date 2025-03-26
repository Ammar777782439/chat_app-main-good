from kafka import KafkaProducer
import json
import time

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
        'bootstrap_servers': '192.168.117.128:9094',  # يمكنك تغييره إلى localhost:9094 لاختبار الوسيط الآخر
        'client_id': 'python-test-producer',
        # لا حاجة لإعداد broker.address.family في kafka-python، فإنه يدير هذه الإعدادات تلقائيًا
    }

    print(f"\nاختبار الاتصال بـ Kafka على {config['bootstrap_servers']}...")

    # إنشاء منتج Kafka
    producer = KafkaProducer(
        **config,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')  # تحويل القيمة إلى JSON
    )

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

        # طباعة الرسالة التي سيتم إرسالها
        print(f"إرسال: {message}")

        # إرسال الرسالة إلى Kafka
        producer.send(
            topic=topic,
            key=str(i).encode('utf-8'),  # تحويل المفتاح إلى بايتات
            value=message
        )

        # انتظار قليلاً بين الرسائل
        time.sleep(1)

    # انتظار إرسال جميع الرسائل
    producer.flush()
    print("تم إرسال جميع الرسائل بنجاح")

if __name__ == "__main__":
    test_producer()
