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
        # Get the room name from the URL route
        self.room_name = self.scope['url_route']['kwargs']['room_name']

        # Get the usernames of both users
        user1 = self.scope['user'].username
        user2 = self.room_name

        # Create a unique group name by sorting and joining the usernames
        self.room_group_name = f"chat_{''.join(sorted([user1, user2]))}"

        # Join the room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.

        This method is called when a WebSocket connection is closed. It removes
        the channel from the room group.

        Args:
            close_code: The code indicating why the connection was closed.
        """
        # Leave the room group
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
        # Parse the JSON data
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
                # Broadcast the updated message to the room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',  # Event handler method name
                        'sender': sender.username,
                        'receiver': receiver.username,
                        'message': message,
                        'message_id': message_id  # Include message_id for updates
                    }
                )
        else:
            # Save new message to the database
            saved_message = await self.save_message(sender, receiver, message)
            
        #    نمط ال observers يقوم ب اخطار جميع المتصلين ب التغيرات من خلال داله 
            # Broadcast the new message to the room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',  # Event handler method name
                    'sender': sender.username,
                    'receiver': receiver.username,
                    'message': message,
                    'id': saved_message.id  # Include the new message's ID
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

        # Prepare response data for the WebSocket
        response_data = {
            'sender': sender,
            'receiver': receiver,
            'message': message
        }

        # Add message_id if this is an update to an existing message
        if 'message_id' in event:
            response_data['message_id'] = event['message_id']

        # Add id if this is a new message
        if 'id' in event:
            response_data['id'] = event['id']

        # Send the message to the WebSocket (to the client)
        await self.send(text_data=json.dumps(response_data))

    @sync_to_async
    def save_message(self, sender, receiver, message):
        """
        Save a new message to the database.

        This method creates a new Message object in the database with the
        specified sender, receiver, and content.

        Args:
            sender: The User object of the message sender.
            receiver: The User object of the message receiver.
            message: The content of the message.

        Returns:
            Message: The newly created Message object.
        """
        return Message.objects.create(sender=sender, receiver=receiver, content=message)

    @sync_to_async
    def update_message(self, message_id, sender, new_content):
        """
        Update an existing message in the database.

        This method updates the content of an existing message. It verifies that
        the message exists and that the sender is the owner of the message before
        updating it.

        Args:
            message_id: The ID of the message to update.
            sender: The User object of the message sender (for verification).
            new_content: The new content for the message.

        Returns:
            bool: True if the message was updated successfully, False otherwise.
        """
        try:
            # Get the message and verify ownership
            message = Message.objects.get(id=message_id, sender=sender)
            # Update the content
            message.content = new_content
            message.save()
            return True
        except Message.DoesNotExist:
            # Message doesn't exist or doesn't belong to the sender
            return False

    @sync_to_async
    def get_receiver_user(self):
        """
        Get the User object for the receiver.

        This method retrieves the User object for the receiver based on the
        room_name, which is expected to be the username of the receiver.

        Returns:
            User: The User object for the receiver.

        Raises:
            User.DoesNotExist: If no user with the specified username exists.
        """
        return User.objects.get(username=self.room_name)


