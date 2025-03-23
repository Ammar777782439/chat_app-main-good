**# دليل الحصول على واستخدام توكنات المصادقة**  

هذا الدليل بيوضح لك كيف تحصل على **توكن المصادقة** للمستخدمين وكيف تستخدمه في تطبيق الدردشة.  

---

## **🔹 لمحة سريعة عن المصادقة**  

التطبيق يستخدم **3 أنواع** من المصادقة:  
1. **مصادقة التوكن (Token Authentication)** → خاصة بـ **API**  
2. **مصادقة الجلسة (Session Authentication)** → للاستخدام في **واجهة الموقع**  
3. **مصادقة OAuth2** → لو تريد **تربط التطبيق مع Google أو خدمات ثانية**  

---

## **🔹 كيف تنشئ التوكنات؟**  

التوكن ينشئ **تلقائيًا** لما يتم إنشاء حساب مستخدم جديد، وهذا يتم عبر **إشارة (Signal)** في النظام:  

```python
# ملف users/signals.py
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
```  

---

## **🔹 كيف تحصل على توكن المستخدم؟**  

### **✅ 1. جلب توكن المستخدم الحالي**  

لو تريد تحصل على **توكن المستخدم المسجل حاليًا**:  

```python
from rest_framework.authtoken.models import Token

def get_user_token(user):
    token, created = Token.objects.get_or_create(user=user)
    return token.key
```  

### **✅ 2. جلب التوكن عبر API**  

بعد تسجيل الدخول، المستخدم يقدر يحصل على التوكن من نقطة النهاية التالية:  

```
GET /api/token/
```  

🔸 **مثال على الاستجابة:**  
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```  

### **✅ 3. جلب توكنات جميع المستخدمين (للمسؤولين فقط)**  

لو أنت **أدمن (مسؤول)** وتحتاج **تحصل على توكنات كل المستخدمين**:  

```python
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

def get_all_user_tokens():
    users = User.objects.all()
    tokens = {}
    
    for user in users:
        token, created = Token.objects.get_or_create(user=user)
        tokens[user.username] = token.key
        
    return tokens
```  

---

## **🔹 كيف تستخدم التوكنات في المصادقة؟**  

### **✅ 1. استخدام التوكن في الطلبات HTTP**  

عشان تستخدم التوكن في **الطلبات (Requests)**، أضفه في **الرأس (Header)** بهذا الشكل:  

```
Authorization: Token your_token_here
```  

🔸 **مثال باستخدام `curl`**:  
```bash
curl -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" http://127.0.0.1:8000/api/messages/
```  

🔸 **مثال باستخدام JavaScript (`Fetch API`)**:  
```javascript
fetch('http://127.0.0.1:8000/api/messages/', {
  method: 'GET',
  headers: {
    'Authorization': 'Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b',
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data));
```  

---

### **✅ 2. استخدام التوكن في تطبيقات Flutter**  

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<Map<String, dynamic>> fetchMessages() async {
  final response = await http.get(
    Uri.parse('http://127.0.0.1:8000/api/messages/'),
    headers: {
      'Authorization': 'Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b',
      'Content-Type': 'application/json',
    },
  );

  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('فشل في جلب الرسائل');
  }
}
```  

---

## **🔹 كيف تخزن التوكنات في تطبيقات الويب؟**  

### **✅ 1. تخزين التوكن بعد تسجيل الدخول**  

```javascript
function storeToken(token) {
  localStorage.setItem('authToken', token);
}
```  

### **✅ 2. استرجاع التوكن لاستخدامه في الطلبات**  

```javascript
function getStoredToken() {
  return localStorage.getItem('authToken');
}
```  

### **✅ 3. استخدام التوكن في الطلبات**  

```javascript
function fetchWithAuth(url, options = {}) {
  const token = getStoredToken();
  
  if (!token) {
    window.location.href = '/login/';
    return;
  }
  
  const authOptions = {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Token ${token}`,
    },
  };
  
  return fetch(url, authOptions);
}
```  

---

## **🔹 كيف تعيد إنشاء التوكنات؟**  

لو احتجت **تحذف التوكن القديم وتعمل واحد جديد**، تقدر تستخدم هذا الكود:  

```python
from rest_framework.authtoken.models import Token

def regenerate_user_token(user):
    Token.objects.filter(user=user).delete()
    new_token = Token.objects.create(user=user)
    
    return new_token.key
```  

---

## **🔹 ملاحظات هامة 🛑**  

✅ **أمان التوكنات**: التوكنات مثل كلمات المرور، **لا تخزنها في مكان غير آمن أو تشاركها مع أي شخص**.  
✅ **مدة صلاحية التوكنات**: التوكنات الحالية **ما تنتهي صلاحيتها**، لو تحتاج **توكنات تنتهي صلاحيتها** استخدم `django-rest-framework-simplejwt`.  
✅ **استخدم HTTPS**: في بيئة الإنتاج، **لازم** تستخدم **HTTPS** في جميع الطلبات عشان تحمي التوكنات من السرقة.  
✅ **إعادة توليد التوكن**: لو حصل تسريب **تقدر تعيد إنشائه باستخدام `regenerate_user_token`**.  

---

## **💡 الخلاصة**  

توكنات المصادقة **طريقة آمنة وسريعة** للتحقق من هوية المستخدمين. 🔒  
وباستخدام هذي الأكواد، تقدر **تدير التوكنات وتستخدمها بسهولة** في تطبيقك. 🚀  

**🎯 لو عندك أي استفسار أو تحتاج كود إضافي، خبرني! 😉**
