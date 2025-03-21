"""WebSocket consumers for the chat application.

This module contains the WebSocket consumer classes that handle real-time
communication between users in the chat application. The consumers manage
WebSocket connections, message sending/receiving, and database operations.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Message
from asgiref.sync import sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time chat communication.

    This consumer manages WebSocket connections for the chat application, including
    connecting users to chat rooms, sending and receiving messages, and updating
    or deleting messages in real-time.

    The consumer uses Django Channels to handle WebSocket connections and groups,
    and interacts with the database using asynchronous methods.
    """

    async def connect(self):
        """
        Handle WebSocket connection.

        This method is called when a WebSocket connection is established. It extracts
        the room name from the URL, creates a unique group name for the chat room,
        adds the channel to the group, and accepts the connection.

        The group name is created by sorting and joining the usernames of both users
        to ensure that the same group is used regardless of who initiated the chat.
        """
        # جلب اسم الغرفة من الرابط
        self.room_name = self.scope['url_route']['kwargs']['room_name']

        # جلب اسم المستخدمين الاثنين
        user1 = self.scope['user'].username
        user2 = self.room_name

        # تكوين اسم مجموعة فريد بحيث يكون نفسه بغض النظر عن من بدأ المحادثة
        self.room_group_name = f"chat_{''.join(sorted([user1, user2]))}"

        # إضافة القناة إلى مجموعة الغرفة
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # قبول الاتصال عبر WebSocket
        await self.accept()

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.

        This method is called when a WebSocket connection is closed. It removes
        the channel from the room group.

        Args:
            close_code: The code indicating why the connection was closed.
        """
        # إزالة القناة من مجموعة الغرفة عند قطع الاتصال
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Handle receiving messages from WebSocket.

        This method is called when a message is received from the WebSocket. It processes
        the message data, determines if it's a new message or an update to an existing one,
        saves or updates the message in the database, and broadcasts it to all users in the room.

        Args:
            text_data: The JSON string containing the message data.
        """
        # تحليل البيانات المستلمة
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = self.scope['user']
        receiver = await self.get_receiver_user()

        # التحقق هل هي رسالة جديدة أو تحديث لرسالة موجودة
        message_id = text_data_json.get('message_id', None)

        if message_id:
            # تحديث الرسالة
            updated = await self.update_message(message_id, sender, message)
            if updated:
                # إرسال التحديث إلى جميع المشتركين في الغرفة
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
        else:
            # حفظ الرسالة الجديدة في قاعدة البيانات
            saved_message = await self.save_message(sender, receiver, message)

            # إخطار جميع المستخدمين بالرسالة الجديدة
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
        Handle chat messages sent to the room group.

        This method is called when a message is received from the room group.
        It sends the message to the WebSocket for the client to receive.

        Args:
            event: The event data containing the message information.
        """
        message = event['message']
        sender = event['sender']
        receiver = event['receiver']

        # تجهيز البيانات لإرسالها إلى العميل
        response_data = {
            'sender': sender,
            'receiver': receiver,
            'message': message
        }

        if 'message_id' in event:
            response_data['message_id'] = event['message_id']

        if 'id' in event:
            response_data['id'] = event['id']

        # إرسال البيانات عبر WebSocket
        await self.send(text_data=json.dumps(response_data))

    @sync_to_async
    def save_message(self, sender, receiver, message):
        """
        Save a new message to the database.
        """
        return Message.objects.create(sender=sender, receiver=receiver, content=message)

    @sync_to_async
    def update_message(self, message_id, sender, new_content):
        """
        Update an existing message in the database.
        """
        try:
            # البحث عن الرسالة والتأكد من ملكية المرسل لها
            message = Message.objects.get(id=message_id, sender=sender)
            message.content = new_content
            message.save()
            return True
        except Message.DoesNotExist:
            return False

    @sync_to_async
    def get_receiver_user(self):
        """
        Get the User object for the receiver.
        """
        try:
            return User.objects.get(username=self.room_name)
        except User.DoesNotExist:
            return self.scope['user']
