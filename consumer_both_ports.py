"""
سكريبت مستهلك يستخدم كلا المنفذين 9093 و 9094.
"""

from confluent_kafka import Consumer, KafkaError
import time

def consumer_both_ports():
    """
    مستهلك يستخدم كلا المنفذين 9093 و 9094.
    """
    # إعدادات المستهلك
    config = {
        'bootstrap.servers': 'localhost:9093,localhost:9094',
        'group.id': 'consumer-both-ports',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': True,
        'auto.commit.interval.ms': 1000,
        'socket.timeout.ms': 10000,
        'session.timeout.ms': 10000,
        'max.poll.interval.ms': 300000,
        'heartbeat.interval.ms': 3000
    }
    
    # إنشاء مستهلك Kafka
    consumer = Consumer(config)
    
    # اسم الموضوع
    topic = 'test_topic'
    
    # الاشتراك في الموضوع
    consumer.subscribe([topic])
    
    print(f"بدء الاستماع إلى الموضوع {topic} على المنفذين 9093 و 9094...")
    
    try:
        # قراءة الرسائل لمدة 30 ثانية
        end_time = time.time() + 30
        message_count = 0
        
        while time.time() < end_time:
            # محاولة قراءة رسالة
            msg = consumer.poll(1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(f"وصلنا إلى نهاية القسم {msg.partition()}")
                else:
                    print(f"خطأ: {msg.error()}")
                continue
            
            # طباعة الرسالة
            print(f"استلام: {msg.value().decode('utf-8')}")
            message_count += 1
    
    except KeyboardInterrupt:
        print("تم إيقاف المستهلك")
    
    finally:
        # إغلاق المستهلك
        consumer.close()
        print(f"تم استلام {message_count} رسائل")

if __name__ == "__main__":
    consumer_both_ports()
