# اختبار Kafka باستخدام Python

هذا المشروع يحتوي على أدوات بسيطة لاختبار Kafka باستخدام Python.

## المتطلبات

- Python 3.6+
- مكتبة confluent-kafka
- خادم Kafka يعمل (على المنفذ 9093 أو 9094)

## التثبيت

1. تثبيت مكتبة confluent-kafka:

```bash
pip install confluent-kafka
```

2. التأكد من أن Kafka يعمل:

```bash
docker-compose ps
```

## الملفات

- `kafka_producer_test.py`: اختبار منتج Kafka فقط
- `kafka_consumer_test.py`: اختبار مستهلك Kafka فقط
- `kafka_test.py`: اختبار كامل (منتج ومستهلك معًا)

## كيفية الاستخدام

### 1. إنشاء موضوع في Kafka

قبل تشغيل الاختبارات، تأكد من وجود موضوع `test_topic` في Kafka. يمكنك إنشاؤه من خلال Kafdrop:

1. افتح المتصفح وانتقل إلى `http://localhost:9000`
2. انقر على "Create Topic"
3. أدخل "test_topic" كاسم للموضوع
4. اضبط عدد الأقسام (Partitions) على 1 (أو أكثر)
5. انقر على "Create"

### 2. تشغيل المنتج فقط

```bash
python kafka_producer_test.py
```

أو

```bash
python kafka_test.py producer
```

### 3. تشغيل المستهلك فقط

```bash
python kafka_consumer_test.py
```

أو

```bash
python kafka_test.py consumer
```

### 4. تشغيل الاختبار الكامل (منتج ومستهلك معًا)

```bash
python kafka_test.py
```

### 5. تحديد وسيط Kafka وموضوع مختلفين

```bash
python kafka_test.py producer localhost:9094 my_topic
python kafka_test.py consumer localhost:9094 my_topic
```

## ملاحظات

- تأكد من أن Kafka يعمل وأنه يمكن الوصول إليه عبر المنفذ المحدد (9093 أو 9094).
- يمكنك تعديل إعدادات المنتج والمستهلك في الملفات حسب احتياجاتك.
- إذا واجهت مشاكل في الاتصال، تحقق من إعدادات Kafka وتأكد من أن المنافذ مفتوحة.

## استكشاف الأخطاء وإصلاحها

### مشكلة: لا يمكن الاتصال بـ Kafka

تحقق من:
- أن حاويات Docker تعمل: `docker-compose ps`
- أن المنافذ مفتوحة: `telnet localhost 9093`
- أن Kafdrop يعمل: افتح `http://localhost:9000` في المتصفح

### مشكلة: لا يمكن إنشاء موضوع

تحقق من:
- أن لديك صلاحيات كافية
- أن اسم الموضوع صحيح (بدون أحرف خاصة)
- أن عدد الأقسام والنسخ المتماثلة ضمن الحدود المسموح بها

### مشكلة: لا يتم استلام الرسائل

تحقق من:
- أن المنتج والمستهلك يستخدمان نفس اسم الموضوع
- أن المستهلك مشترك في الموضوع الصحيح
- أن إعداد `auto.offset.reset` مضبوط على 'earliest' للحصول على جميع الرسائل
