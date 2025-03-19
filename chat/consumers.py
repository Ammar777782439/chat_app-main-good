# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Message
from asgiref.sync import sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        user1 = self.scope['user'].username
        user2 = self.room_name
        self.room_group_name = f"chat_{''.join(sorted([user1, user2]))}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = self.scope['user']
        receiver = await self.get_receiver_user()

        # Check if this is a new message or an update to an existing message
        message_id = text_data_json.get('message_id', None)

        if message_id:
            # Update existing message
            updated = await self.update_message(message_id, sender, message)
            if updated:
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
            # Save new message
            saved_message = await self.save_message(sender, receiver, message)

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
        message = event['message']
        sender = event['sender']
        receiver = event['receiver']

        # Prepare response data
        response_data = {
            'sender': sender,
            'receiver': receiver,
            'message': message
        }

        # Add message_id if this is an update
        if 'message_id' in event:
            response_data['message_id'] = event['message_id']

        # Add id if this is a new message
        if 'id' in event:
            response_data['id'] = event['id']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(response_data))

    @sync_to_async
    def save_message(self, sender, receiver, message):
        return Message.objects.create(sender=sender, receiver=receiver, content=message)

    @sync_to_async
    def update_message(self, message_id, sender, new_content):
        try:
            message = Message.objects.get(id=message_id, sender=sender)
            message.content = new_content
            message.save()
            return True
        except Message.DoesNotExist:
            return False

    @sync_to_async
    def get_receiver_user(self):
        return User.objects.get(username=self.room_name)


