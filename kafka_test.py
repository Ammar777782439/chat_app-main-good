from confluent_kafka import Producer, Consumer, KafkaError
import json
import time
import threading
import sys

def delivery_report(err, msg):
    """
    تقرير تسليم الرسائل
    """
    if err is not None:
        print(f"فشل تسليم الرسالة: {err}")
    else:
        print(f"تم تسليم الرسالة إلى {msg.topic()} [قسم {msg.partition()}] عند الموضع {msg.offset()}")

def run_producer(bootstrap_servers, topic):
    """
    تشغيل منتج Kafka
    """
    # إعدادات المنتج
    config = {
        'bootstrap.servers': bootstrap_servers,
        'client.id': 'python-test-producer',
        # إضافة إعدادات إضافية لتجنب مشكلة حل أسماء المضيفين
        'broker.address.family': 'v4'  # استخدام IPv4 فقط
    }

    # إنشاء منتج Kafka
    producer = Producer(config)

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

def run_consumer(bootstrap_servers, topic):
    """
    تشغيل مستهلك Kafka
    """
    # إعدادات المستهلك
    config = {
        'bootstrap.servers': bootstrap_servers,
        'group.id': 'python-test-consumer',
        'auto.offset.reset': 'earliest',  # بدء القراءة من أقدم رسالة
        # إضافة إعدادات إضافية لتجنب مشكلة حل أسماء المضيفين
        'broker.address.family': 'v4'  # استخدام IPv4 فقط
    }

    # إنشاء مستهلك Kafka
    consumer = Consumer(config)

    # الاشتراك في الموضوع
    consumer.subscribe([topic])

    # عدد الرسائل التي سيتم قراءتها
    message_count = 0
    max_messages = 10

    # وقت البدء
    start_time = time.time()

    # قراءة الرسائل
    try:
        while message_count < max_messages:
            # التحقق من انتهاء المهلة (30 ثانية)
            if time.time() - start_time > 30:
                print("انتهت المهلة. لم يتم استلام المزيد من الرسائل.")
                break

            # محاولة قراءة رسالة
            msg = consumer.poll(1.0)

            # التحقق من وجود رسالة
            if msg is None:
                continue

            # التحقق من وجود خطأ
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # وصلنا إلى نهاية القسم
                    print(f"وصلنا إلى نهاية القسم {msg.partition()}")
                else:
                    print(f"خطأ: {msg.error()}")
                continue

            # معالجة الرسالة
            try:
                # قراءة قيمة الرسالة
                message_value = msg.value().decode('utf-8')

                # تحويل الرسالة من JSON
                message_data = json.loads(message_value)

                # طباعة الرسالة
                print(f"استلام: {message_data}")

                # زيادة عداد الرسائل
                message_count += 1
            except Exception as e:
                print(f"خطأ في معالجة الرسالة: {e}")

    except KeyboardInterrupt:
        print("تم إيقاف المستهلك")

    finally:
        # إغلاق المستهلك
        consumer.close()
        print(f"تم استلام {message_count} رسائل")

def test_kafka():
    """
    اختبار Kafka (منتج ومستهلك)
    """
    # المعلمات
    bootstrap_servers = 'localhost:9093'  # يمكنك تغييره إلى localhost:9094 لاختبار الوسيط الآخر
    topic = 'test_topic'

    print(f"\nاختبار الاتصال بـ Kafka على {bootstrap_servers}...")

    # إنشاء موضوع جديد (اختياري)
    # يمكنك إنشاء الموضوع من خلال Kafdrop أو باستخدام أدوات Kafka

    # تشغيل المستهلك في خيط منفصل
    consumer_thread = threading.Thread(target=run_consumer, args=(bootstrap_servers, topic))
    consumer_thread.daemon = True
    consumer_thread.start()

    # انتظار قليلاً لبدء المستهلك
    time.sleep(2)

    # تشغيل المنتج
    run_producer(bootstrap_servers, topic)

    # انتظار انتهاء المستهلك
    consumer_thread.join(timeout=30)

    print("اكتمل الاختبار")

if __name__ == "__main__":
    # التحقق من وجود المعلمات
    if len(sys.argv) > 1:
        if sys.argv[1] == 'producer':
            # تشغيل المنتج فقط
            bootstrap_servers = sys.argv[2] if len(sys.argv) > 2 else 'localhost:9093'
            topic = sys.argv[3] if len(sys.argv) > 3 else 'test_topic'
            run_producer(bootstrap_servers, topic)
        elif sys.argv[1] == 'consumer':
            # تشغيل المستهلك فقط
            bootstrap_servers = sys.argv[2] if len(sys.argv) > 2 else 'localhost:9093'
            topic = sys.argv[3] if len(sys.argv) > 3 else 'test_topic'
            run_consumer(bootstrap_servers, topic)
        else:
            # تشغيل الاختبار الكامل
            test_kafka()
    else:
        # تشغيل الاختبار الكامل
        test_kafka()
