"""
Example of Kafka integration with the chat application.

This module demonstrates how to integrate Kafka with the chat application
for real-time message processing and event handling.
"""

import json
import threading
from django.contrib.auth.models import User
from .models import Message
from .kafka_utils import send_message_to_kafka, get_kafka_consumer
import logging
from asgiref.sync import sync_to_async
import asyncio

logger = logging.getLogger(__name__)

# موضوعات Kafka
CHAT_MESSAGES_TOPIC = 'chat_messages'
MESSAGE_UPDATES_TOPIC = 'message_updates'
MESSAGE_DELETIONS_TOPIC = 'message_deletions'

# مثال على إرسال رسالة جديدة إلى Kafka
def send_new_message_to_kafka(sender_username, receiver_username, message_content, message_id):
    """
    Send a new chat message to Kafka.
    
    Args:
        sender_username (str): The username of the message sender.
        receiver_username (str): The username of the message receiver.
        message_content (str): The content of the message.
        message_id (int): The ID of the message in the database.
        
    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    message_data = {
        'type': 'new_message',
        'sender': sender_username,
        'receiver': receiver_username,
        'content': message_content,
        'message_id': message_id,
        'timestamp': str(Message.objects.get(id=message_id).timestamp)
    }
    
    return send_message_to_kafka(CHAT_MESSAGES_TOPIC, message_data)

# مثال على إرسال تحديث رسالة إلى Kafka
def send_message_update_to_kafka(message_id, new_content, sender_username):
    """
    Send a message update to Kafka.
    
    Args:
        message_id (int): The ID of the message being updated.
        new_content (str): The new content of the message.
        sender_username (str): The username of the message sender.
        
    Returns:
        bool: True if the update was sent successfully, False otherwise.
    """
    update_data = {
        'type': 'message_update',
        'message_id': message_id,
        'new_content': new_content,
        'sender': sender_username,
        'timestamp': str(Message.objects.get(id=message_id).timestamp)
    }
    
    return send_message_to_kafka(MESSAGE_UPDATES_TOPIC, update_data)

# مثال على إرسال حذف رسالة إلى Kafka
def send_message_deletion_to_kafka(message_id, sender_username):
    """
    Send a message deletion to Kafka.
    
    Args:
        message_id (int): The ID of the message being deleted.
        sender_username (str): The username of the message sender.
        
    Returns:
        bool: True if the deletion was sent successfully, False otherwise.
    """
    deletion_data = {
        'type': 'message_deletion',
        'message_id': message_id,
        'sender': sender_username,
        'timestamp': str(Message.objects.get(id=message_id).timestamp)
    }
    
    return send_message_to_kafka(MESSAGE_DELETIONS_TOPIC, deletion_data)

# مثال على معالجة رسائل Kafka
def process_kafka_message(message_data):
    """
    Process a message received from Kafka.
    
    Args:
        message_data (dict): The message data to process.
    """
    message_type = message_data.get('type')
    
    if message_type == 'new_message':
        # معالجة رسالة جديدة
        sender_username = message_data.get('sender')
        receiver_username = message_data.get('receiver')
        content = message_data.get('content')
        
        try:
            sender = User.objects.get(username=sender_username)
            receiver = User.objects.get(username=receiver_username)
            
            # إنشاء رسالة جديدة في قاعدة البيانات
            Message.objects.create(
                sender=sender,
                receiver=receiver,
                content=content
            )
            logger.info(f"Created new message from {sender_username} to {receiver_username}")
        except User.DoesNotExist:
            logger.error(f"User not found: {sender_username} or {receiver_username}")
        except Exception as e:
            logger.error(f"Error processing new message: {e}")
    
    elif message_type == 'message_update':
        # معالجة تحديث رسالة
        message_id = message_data.get('message_id')
        new_content = message_data.get('new_content')
        
        try:
            message = Message.objects.get(id=message_id)
            message.content = new_content
            message.save()
            logger.info(f"Updated message {message_id}")
        except Message.DoesNotExist:
            logger.error(f"Message not found: {message_id}")
        except Exception as e:
            logger.error(f"Error processing message update: {e}")
    
    elif message_type == 'message_deletion':
        # معالجة حذف رسالة
        message_id = message_data.get('message_id')
        
        try:
            message = Message.objects.get(id=message_id)
            message.delete()
            logger.info(f"Deleted message {message_id}")
        except Message.DoesNotExist:
            logger.error(f"Message not found: {message_id}")
        except Exception as e:
            logger.error(f"Error processing message deletion: {e}")

# بدء مستهلك Kafka في خيط منفصل
def start_kafka_consumer(topic, group_id=None):
    """
    Start a Kafka consumer in a separate thread.
    
    Args:
        topic (str): The Kafka topic to consume messages from.
        group_id (str, optional): Consumer group ID. Defaults to None.
        
    Returns:
        threading.Thread: The thread running the consumer.
    """
    def consumer_thread():
        consumer = get_kafka_consumer(topic, group_id)
        if not consumer:
            logger.error(f"Failed to create Kafka consumer for topic {topic}")
            return
        
        try:
            for message in consumer:
                process_kafka_message(message.value)
        except Exception as e:
            logger.error(f"Error in Kafka consumer thread: {e}")
        finally:
            consumer.close()
    
    thread = threading.Thread(target=consumer_thread, daemon=True)
    thread.start()
    return thread

# مثال على كيفية بدء مستهلكي Kafka عند بدء تشغيل التطبيق
def start_kafka_consumers():
    """
    Start all Kafka consumers for the chat application.
    
    This function should be called when the application starts.
    """
    # بدء مستهلك لرسائل الدردشة الجديدة
    chat_messages_thread = start_kafka_consumer(
        CHAT_MESSAGES_TOPIC, 
        group_id='chat_messages_group'
    )
    
    # بدء مستهلك لتحديثات الرسائل
    message_updates_thread = start_kafka_consumer(
        MESSAGE_UPDATES_TOPIC, 
        group_id='message_updates_group'
    )
    
    # بدء مستهلك لحذف الرسائل
    message_deletions_thread = start_kafka_consumer(
        MESSAGE_DELETIONS_TOPIC, 
        group_id='message_deletions_group'
    )
    
    logger.info("Started Kafka consumers for chat application")
    
    return {
        'chat_messages_thread': chat_messages_thread,
        'message_updates_thread': message_updates_thread,
        'message_deletions_thread': message_deletions_thread
    }

# مثال على كيفية دمج Kafka مع مستهلك WebSocket
class KafkaEnabledChatConsumer:
    """
    Example of how to integrate Kafka with the WebSocket consumer.
    
    This is a simplified example showing how you might modify your existing
    ChatConsumer to use Kafka for message processing.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        # الكود الحالي للاتصال
        pass
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # الكود الحالي للانفصال
        pass
    
    async def receive(self, text_data):
        """
        Handle receiving messages from WebSocket.
        
        This method is modified to send messages to Kafka instead of
        directly processing them.
        """
        text_data_json = json.loads(text_data)
        sender = self.scope['user']
        receiver = await self.get_receiver_user()
        
        message = text_data_json.get('message', '')
        message_id = text_data_json.get('message_id', None)
        delete_message_id = text_data_json.get('delete_message_id', None)
        
        # حالة حذف رسالة
        if delete_message_id:
            # التحقق من أن المستخدم هو مالك الرسالة
            is_owner = await self.check_message_owner(delete_message_id, sender)
            if is_owner:
                # إرسال حذف الرسالة إلى Kafka
                await sync_to_async(send_message_deletion_to_kafka)(
                    delete_message_id, 
                    sender.username
                )
                
                # إخطار المستخدمين الآخرين بالحذف
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'sender': sender.username,
                        'receiver': receiver.username,
                        'deleted_message_id': delete_message_id
                    }
                )
        
        # حالة تحديث رسالة موجودة
        elif message_id:
            # التحقق من أن المستخدم هو مالك الرسالة
            is_owner = await self.check_message_owner(message_id, sender)
            if is_owner:
                # إرسال تحديث الرسالة إلى Kafka
                await sync_to_async(send_message_update_to_kafka)(
                    message_id, 
                    message, 
                    sender.username
                )
                
                # إخطار المستخدمين الآخرين بالتحديث
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'sender': sender.username,
                        'receiver': receiver.username,
                        'message': message,
                        'message_id': message_id
                    }
                )
        
        # حالة إرسال رسالة جديدة
        else:
            # حفظ الرسالة الجديدة في قاعدة البيانات
            saved_message = await self.save_message(sender, receiver, message)
            
            # إرسال الرسالة الجديدة إلى Kafka
            await sync_to_async(send_new_message_to_kafka)(
                sender.username, 
                receiver.username, 
                message, 
                saved_message.id
            )
            
            # إخطار المستخدمين الآخرين بالرسالة الجديدة
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'sender': sender.username,
                    'receiver': receiver.username,
                    'message': message,
                    'id': saved_message.id
                }
            )
    
    async def chat_message(self, event):
        """
        Send chat message to WebSocket.
        
        This method remains largely unchanged as it's responsible for
        sending messages to the WebSocket client.
        """
        # الكود الحالي لإرسال الرسائل
        pass
