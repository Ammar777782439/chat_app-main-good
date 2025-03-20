"""Tests for WebSocket consumers.

This module contains tests for the WebSocket consumers used in the chat application.
It tests the connection, message sending/receiving, and other WebSocket functionality.
"""

import json
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from chat.models import Message
from chat_app.asgi import application


class ChatConsumerTest(TransactionTestCase):
    """Test cases for the ChatConsumer WebSocket consumer."""

    async def test_connect(self):
        """Test WebSocket connection."""
        # Create a test user
        await self.create_user('testuser', 'test@example.com', 'testpassword')
        
        # Connect to the WebSocket
        communicator = WebsocketCommunicator(application, "/ws/chat/testuser/")
        connected, _ = await communicator.connect()
        
        # Test that the connection was accepted
        self.assertTrue(connected)
        
        # Close the connection
        await communicator.disconnect()

    async def test_receive_json(self):
        """Test receiving a message through WebSocket."""
        # Create test users
        sender = await self.create_user('sender', 'sender@example.com', 'password')
        receiver = await self.create_user('receiver', 'receiver@example.com', 'password')
        
        # Connect to the WebSocket
        communicator = WebsocketCommunicator(application, "/ws/chat/receiver/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Send a message
        await communicator.send_json_to({
            'type': 'chat_message',
            'message': 'Hello, receiver!',
            'sender': sender.id,
            'receiver': receiver.id
        })
        
        # Receive the response
        response = await communicator.receive_json_from()
        
        # Check the response
        self.assertEqual(response['message'], 'Hello, receiver!')
        self.assertEqual(response['sender'], sender.id)
        
        # Close the connection
        await communicator.disconnect()

    async def test_chat_message(self):
        """Test the chat_message method."""
        # Create test users
        sender = await self.create_user('sender2', 'sender2@example.com', 'password')
        receiver = await self.create_user('receiver2', 'receiver2@example.com', 'password')
        
        # Connect to the WebSocket
        communicator = WebsocketCommunicator(application, "/ws/chat/receiver2/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Send a chat message event
        event = {
            'type': 'chat_message',
            'message': 'Test message',
            'sender': sender.id,
            'receiver': receiver.id,
            'timestamp': '2023-01-01T12:00:00Z'
        }
        
        await communicator.send_json_to(event)
        
        # Receive the response
        response = await communicator.receive_json_from()
        
        # Check the response
        self.assertEqual(response['message'], 'Test message')
        self.assertEqual(response['sender'], sender.id)
        self.assertEqual(response['receiver'], receiver.id)
        
        # Close the connection
        await communicator.disconnect()

    async def test_update_message(self):
        """Test updating a message through WebSocket."""
        # Create test users
        sender = await self.create_user('sender3', 'sender3@example.com', 'password')
        receiver = await self.create_user('receiver3', 'receiver3@example.com', 'password')
        
        # Create a test message
        message = await self.create_message(sender, receiver, 'Original message')
        
        # Connect to the WebSocket
        communicator = WebsocketCommunicator(application, "/ws/chat/receiver3/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Send an update message event
        await communicator.send_json_to({
            'type': 'update_message',
            'message_id': message.id,
            'content': 'Updated message'
        })
        
        # Receive the response
        response = await communicator.receive_json_from()
        
        # Check the response
        self.assertEqual(response['type'], 'update_message')
        self.assertEqual(response['message_id'], message.id)
        self.assertEqual(response['content'], 'Updated message')
        
        # Close the connection
        await communicator.disconnect()

    async def test_delete_message(self):
        """Test deleting a message through WebSocket."""
        # Create test users
        sender = await self.create_user('sender4', 'sender4@example.com', 'password')
        receiver = await self.create_user('receiver4', 'receiver4@example.com', 'password')
        
        # Create a test message
        message = await self.create_message(sender, receiver, 'Message to delete')
        
        # Connect to the WebSocket
        communicator = WebsocketCommunicator(application, "/ws/chat/receiver4/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Send a delete message event
        await communicator.send_json_to({
            'type': 'delete_message',
            'message_id': message.id
        })
        
        # Receive the response
        response = await communicator.receive_json_from()
        
        # Check the response
        self.assertEqual(response['type'], 'delete_message')
        self.assertEqual(response['message_id'], message.id)
        
        # Close the connection
        await communicator.disconnect()

    @database_sync_to_async
    def create_user(self, username, email, password):
        """Create a test user."""
        return User.objects.create_user(username=username, email=email, password=password)

    @database_sync_to_async
    def create_message(self, sender, receiver, content):
        """Create a test message."""
        return Message.objects.create(sender=sender, receiver=receiver, content=content)
