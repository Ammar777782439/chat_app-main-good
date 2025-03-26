from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import KafkaError

# إعدادات الاتصال بـ Kafka
bootstrap_servers = '192.168.117.128:9094'

# إنشاء عميل الإداري (AdminClient) لإدارة المواضيع
admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)

# اسم الموضوع الذي ترغب في إنشائه
topic_name = 'my-topic'

# إعدادات الموضوع
new_topic = NewTopic(
    name=topic_name,
    num_partitions=1,  # عدد الأقسام
    replication_factor=1  # عامل التكرار
)

# إنشاء الموضوع
try:
    admin_client.create_topics([new_topic])
    print(f"تم إنشاء الموضوع: {topic_name}")
except KafkaError as e:
    print(f"حدث خطأ أثناء إنشاء الموضوع: {e}")
