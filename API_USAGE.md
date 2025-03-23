# دليل استخدام واجهة برمجة التطبيقات (API)

## المصادقة

هناك ثلاث طرق للمصادقة مع واجهة برمجة التطبيقات:

### 1. الحصول على التوكن باستخدام اسم المستخدم وكلمة المرور (API)

يمكنك الحصول على توكن المصادقة مباشرة عن طريق إرسال اسم المستخدم (أو البريد الإلكتروني) وكلمة المرور إلى نقطة النهاية التالية:

```
POST /api/auth/login/
```

مثال للبيانات المرسلة:

**للمستخدمين العاديين**:
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**لمستخدمي Google OAuth**:
```json
{
  "username": "your_username",
  "password": "",
  "oauth": "true"
}
```

يمكنك أيضًا استخدام البريد الإلكتروني بدلاً من اسم المستخدم في كلتا الحالتين.

مثال باستخدام curl للمستخدمين العاديين:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"username":"your_username","password":"your_password"}' http://127.0.0.1:8000/api/auth/login/
```

مثال باستخدام curl لمستخدمي Google OAuth:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"username":"your_username","password":"","oauth":"true"}' http://127.0.0.1:8000/api/auth/login/
```

الاستجابة في حالة النجاح:
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

### 2. مصادقة الرمز (Token Authentication)

يتم إنشاء رمز المصادقة تلقائيًا عند إنشاء حساب مستخدم جديد. للحصول على الرمز الخاص بك:

1. قم بتسجيل الدخول إلى التطبيق من خلال واجهة المستخدم
2. قم بزيارة: `http://127.0.0.1:8000/api/token/` للحصول على رمز المصادقة الخاص بك
3. استخدم هذا الرمز في جميع طلبات API من خلال إضافة رأس HTTP:
   ```
   Authorization: Token your_token_here
   ```

مثال باستخدام curl:
```bash
curl -H "Authorization: Token your_token_here" http://127.0.0.1:8000/api/messages/
```

### 3. مصادقة الجلسة (Session Authentication)

1. قم بتسجيل الدخول إلى التطبيق من خلال واجهة المستخدم
2. استخدم ملفات تعريف الارتباط (cookies) التي تم إنشاؤها للمصادقة
3. تأكد من إرسال ملفات تعريف الارتباط مع كل طلب API

مثال باستخدام curl:
```bash
curl -b cookies.txt -c cookies.txt http://127.0.0.1:8000/api/messages/
```

## نقاط نهاية الرسائل

### الحصول على الرسائل

```
GET /api/messages/
```

معلمات الاستعلام:
- `user`: تصفية الرسائل حسب اسم المستخدم
- `page`: رقم الصفحة (افتراضي: 1)
- `page_size`: عدد الرسائل في الصفحة (افتراضي: 10، الحد الأقصى: 100)

مثال:
```
GET /api/messages/?user=john&page=1&page_size=20
```

### إرسال رسالة جديدة

```
POST /api/messages/
```

البيانات المطلوبة:
```json
{
  "receiver": "user_id",
  "content": "محتوى الرسالة"
}
```

### تحديث رسالة

```
POST /api/messages/{id}/update_message/
```

البيانات المطلوبة:
```json
{
  "content": "محتوى الرسالة الجديد"
}
```

### حذف رسالة

```
DELETE /api/messages/{id}/delete_message/
```

## واجهة برمجة WebSocket للرسائل في الوقت الفعلي

يوفر التطبيق واجهة WebSocket للتواصل في الوقت الفعلي. يمكنك استخدام WebSocket للحصول على الرسائل الجديدة وتحديثات الرسائل وإشعارات الحذف فور حدوثها.

### الاتصال بـ WebSocket

عنوان الاتصال:
```
ws://your-domain.com/ws/chat/{username}/
```
حيث `{username}` هو اسم المستخدم الذي تريد الدردشة معه.

### إرسال رسالة جديدة

لإرسال رسالة جديدة عبر WebSocket، أرسل JSON بالتنسيق التالي:

```json
{
  "message": "محتوى الرسالة"
}
```

### تحديث رسالة موجودة

لتحديث رسالة موجودة، أرسل JSON بالتنسيق التالي:

```json
{
  "message_id": 123,
  "message": "محتوى الرسالة الجديد"
}
```

### حذف رسالة

لحذف رسالة، أرسل JSON بالتنسيق التالي:

```json
{
  "delete_message_id": 123
}
```

### استقبال الأحداث

ستتلقى أحداثًا من WebSocket بالتنسيقات التالية:

**رسالة جديدة:**
```json
{
  "sender": "username1",
  "receiver": "username2",
  "message": "محتوى الرسالة",
  "id": 123
}
```

**تحديث رسالة:**
```json
{
  "sender": "username1",
  "receiver": "username2",
  "message": "محتوى الرسالة المحدث",
  "message_id": 123
}
```

**حذف رسالة:**
```json
{
  "sender": "username1",
  "receiver": "username2",
  "deleted_message_id": 123
}
```

## ملاحظات هامة

1. يجب أن تكون مصادقًا لاستخدام أي من نقاط النهاية المذكورة أعلاه.
2. يمكنك فقط تحديث أو حذف الرسائل التي أرسلتها.
3. عند استخدام مصادقة الجلسة، تأكد من إرسال رمز CSRF مع طلبات POST/PUT/DELETE.
4. يتم إنشاء توكن المصادقة تلقائيًا عند إنشاء حساب مستخدم جديد.
5. يتم استخدام WebSocket للتواصل في الوقت الفعلي، بينما تستخدم واجهة برمجة التطبيقات REST للعمليات غير المتزامنة.
