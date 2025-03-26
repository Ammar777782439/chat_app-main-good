"""
أمر إدارة لاختبار دمج Kafka مع ChatConsumer.

هذا الأمر يختبر إرسال رسائل الدردشة إلى Kafka باستخدام KafkaChatAgent.
"""

import json
import logging
import asyncio
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from chat.agents.kafka_chat_agent import KafkaChatAgent

# إعداد التسجيل
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    أمر إدارة Django لاختبار دمج Kafka مع ChatConsumer.
    """
    
    help = 'اختبار إرسال رسائل الدردشة إلى Kafka باستخدام KafkaChatAgent'
    
    def add_arguments(self, parser):
        """
        إضافة وسائط الأمر.
        """
        parser.add_argument(
            '--sender',
            type=str,
            help='اسم المستخدم المرسل'
        )
        parser.add_argument(
            '--receiver',
            type=str,
            help='اسم المستخدم المستلم'
        )
        parser.add_argument(
            '--message',
            type=str,
            default='رسالة اختبار من أمر الإدارة',
            help='محتوى الرسالة (الافتراضي: رسالة اختبار من أمر الإدارة)'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='عدد الرسائل للإرسال (الافتراضي: 1)'
        )
    
    def handle(self, *args, **options):
        """
        تنفيذ الأمر.
        """
        # التحقق من تمكين Kafka
        if not getattr(settings, 'KAFKA_ENABLED', False):
            self.stdout.write(self.style.WARNING('Kafka غير ممكّن في الإعدادات'))
            return
        
        # الحصول على معلمات الأمر
        sender_username = options['sender']
        receiver_username = options['receiver']
        message_content = options['message']
        message_count = options['count']
        
        # التحقق من وجود المستخدمين
        try:
            if sender_username:
                sender = User.objects.get(username=sender_username)
                sender_id = sender.id
            else:
                # استخدام أول مستخدم إذا لم يتم تحديد المرسل
                sender = User.objects.first()
                sender_id = sender.id
                sender_username = sender.username
            
            if receiver_username:
                receiver = User.objects.get(username=receiver_username)
                receiver_id = receiver.id
            else:
                # استخدام ثاني مستخدم إذا لم يتم تحديد المستلم
                receiver = User.objects.exclude(id=sender_id).first()
                if not receiver:
                    # إذا لم يكن هناك مستخدم ثانٍ، استخدم المرسل نفسه
                    receiver = sender
                receiver_id = receiver.id
                receiver_username = receiver.username
        
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'المستخدم غير موجود: {sender_username or receiver_username}'))
            return
        
        self.stdout.write(f'اختبار إرسال رسائل الدردشة إلى Kafka:')
        self.stdout.write(f'  - المرسل: {sender_username} (ID: {sender_id})')
        self.stdout.write(f'  - المستلم: {receiver_username} (ID: {receiver_id})')
        self.stdout.write(f'  - الرسالة: {message_content}')
        self.stdout.write(f'  - عدد الرسائل: {message_count}')
        self.stdout.write('')
        
        # إنشاء وكيل Kafka
        agent = KafkaChatAgent.get_instance()
        
        # إنشاء حلقة أحداث
        loop = asyncio.get_event_loop()
        
        # إرسال الرسائل
        for i in range(message_count):
            message = f"{message_content} #{i+1}" if message_count > 1 else message_content
            
            try:
                # إرسال الرسالة
                message_data = loop.run_until_complete(
                    agent.send_chat_message(
                        sender_id=sender_id,
                        receiver_id=receiver_id,
                        content=message,
                        metadata={
                            'action': 'create',
                            'test': True
                        }
                    )
                )
                
                self.stdout.write(self.style.SUCCESS(f'تم إرسال الرسالة: {message} (ID: {message_data["message_id"]})'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'فشل إرسال الرسالة: {str(e)}'))
        
        # تنظيف الموارد
        agent.flush()
        
        self.stdout.write(self.style.SUCCESS('اكتمل اختبار إرسال رسائل الدردشة إلى Kafka'))
