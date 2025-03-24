from confluent_kafka import Consumer, KafkaError
import json
import time

def test_consumer():
    # إعدادات المستهلك
    config = {
        'bootstrap.servers': 'localhost:9093',  # يمكنك تغييره إلى localhost:9094 لاختبار الوسيط الآخر
        'group.id': 'python-test-consumer',
        'auto.offset.reset': 'earliest'  # بدء القراءة من أقدم رسالة
    }
    
    # إنشاء مستهلك Kafka
    consumer = Consumer(config)
    
    # اسم الموضوع
    topic = 'test_topic'
    
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

if __name__ == "__main__":
    test_consumer()
