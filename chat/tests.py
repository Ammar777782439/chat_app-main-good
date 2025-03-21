from django.test import TestCase, Client  # استيراد أدوات الاختبار العادية حق Django
from django.urls import reverse  # استيراد reverse لاستخدام الروابط في الاختبار
from django.contrib.auth.models import User  # استيراد نموذج المستخدم
from rest_framework.test import APITestCase, APIClient  # استيراد أدوات الاختبار الخاصة بالـ API
from rest_framework import status  # استيراد أكواد استجابة الـ HTTP
from chat.models import Message  # استيراد نموذج الرسائل
from chat.serializers import MessageSerializer  # استيراد السيريلايزر حق الرسائل
from django.utils import timezone  # استيراد timezone لاستخدام الوقت والتواريخ

class MessageViewSetTest(APITestCase):
    def setUp(self):
        """إعداد البيانات اللي بنستخدمها في الاختبارات"""
        
        # إنشاء مستخدمين للتجربة
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        
        # إنشاء رسالتين اختبار
        self.message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Hello user2'
        )
        self.message2 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Hi user1'
        )
        
        # تجهيز API Client وتسجيل دخول user1
        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

    def test_get_messages(self):
        """اختبار جلب جميع الرسائل"""
        response = self.client.get('/api/messages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # لازم يكون فيه رسالتين

    def test_get_filtered_messages(self):
        """اختبار جلب الرسائل المرسلة أو المستقبلة من مستخدم معين"""
        response = self.client.get(f'/api/messages/?user={self.user2.username}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # لازم يجيب كل الرسائل بينهم

    def test_create_message(self):
        """اختبار إرسال رسالة جديدة"""
        data = {
            'receiver': self.user2.id,
            'content': 'New test message'
        }
        response = self.client.post('/api/messages/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 3)  # لازم يصير عدد الرسائل 3

    def test_delete_message(self):
        """اختبار حذف رسالة خاصة بالمستخدم"""
        response = self.client.delete(f'/api/messages/{self.message1.id}/delete_message/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Message.objects.count(), 1)  # لازم يتبقى رسالة واحدة فقط

    def test_delete_others_message(self):
        """اختبار محاولة حذف رسالة لشخص ثاني (المفروض يرفض)"""
        response = self.client.delete(f'/api/messages/{self.message2.id}/delete_message/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # ما يسمح له بالحذف

    def test_update_message(self):
        """اختبار تعديل رسالة خاصة بالمستخدم"""
        data = {'content': 'Updated content'}
        response = self.client.post(f'/api/messages/{self.message1.id}/update_message/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.message1.refresh_from_db()  # تحديث البيانات بعد التعديل
        self.assertEqual(self.message1.content, 'Updated content')  # لازم المحتوى يتغير

    def test_update_others_message(self):
        """اختبار محاولة تعديل رسالة شخص ثاني (المفروض يرفض)"""
        data = {'content': 'Updated content'}
        response = self.client.post(f'/api/messages/{self.message2.id}/update_message/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # ما يسمح له بالتعديل

class ChatRoomViewTest(TestCase):
    def setUp(self):
        """إعداد بيانات الاختبار الخاصة بغرف الدردشة"""
        
        # إنشاء مستخدمين للتجربة
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        
        # إنشاء رسالة اختبارية بينهم
        self.message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Hello user2'
        )
        
        # تجهيز Client وتسجيل دخول user1
        self.client = Client()
        self.client.login(username='user1', password='testpass123')

    def test_chat_room_view(self):
        """اختبار صفحة الدردشة عند تسجيل الدخول"""
        response = self.client.get(f'/chat/{self.user2.username}/')
        self.assertEqual(response.status_code, 200)  # الصفحة لازم تفتح عادي
        self.assertTemplateUsed(response, 'chat.html')  # يتأكد إنه استخدم القالب الصح

    def test_chat_room_view_unauthenticated(self):
        """اختبار محاولة دخول صفحة الدردشة بدون تسجيل دخول"""
        self.client.logout()  # تسجيل خروج
        response = self.client.get(f'/chat/{self.user2.username}/')
        self.assertEqual(response.status_code, 302)  # لازم يعيد التوجيه لصفحة تسجيل الدخول

    def test_chat_room_search(self):
        """اختبار البحث عن رسالة داخل صفحة الدردشة"""
        response = self.client.get(f'/chat/{self.user2.username}/?search=Hello')
        self.assertEqual(response.status_code, 200)  # الصفحة تفتح بدون مشاكل
        self.assertTemplateUsed(response, 'chat.html')  # يتأكد إنه استخدم القالب الصح
