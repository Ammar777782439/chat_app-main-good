"""
Tests for Kafka integration in the chat application.

This module contains tests for the Kafka producer and its integration with
the chat application. It tests the sending of messages to Kafka topics and
the handling of Kafka-related errors.
"""

import json
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from chat_app.asgi import application
from chat.kafka_utils import ChatKafkaProducer
from chat.models import Message


class KafkaUtilsTests(TestCase):
    """
    Tests for the Kafka utilities.
    
    This class tests the ChatKafkaProducer class and its methods for sending
    messages to Kafka topics.
    """
    
    def setUp(self):
        """Set up test environment."""
        self.producer_mock = MagicMock()
        self.future_mock = MagicMock()
        self.future_mock.get.return_value = None
        self.producer_mock.send.return_value = self.future_mock
    
    @patch('kafka.KafkaProducer')
    def test_kafka_producer_init(self, mock_kafka_producer):
        """Test the initialization of the Kafka producer."""
        mock_kafka_producer.return_value = self.producer_mock
        
        producer = ChatKafkaProducer(bootstrap_servers='test:9094', topic='test_topic')
        
        # Check that the producer was initialized with the correct parameters
        mock_kafka_producer.assert_called_once()
        self.assertEqual(producer.topic, 'test_topic')
        self.assertIsNotNone(producer.producer)
    
    @patch('kafka.KafkaProducer')
    def test_kafka_producer_send_message(self, mock_kafka_producer):
        """Test sending a message to Kafka."""
        mock_kafka_producer.return_value = self.producer_mock
        
        producer = ChatKafkaProducer(bootstrap_servers='test:9094', topic='test_topic')
        message_data = {'message': 'test message', 'sender': 'test_user'}
        
        result = producer.send_message(message_data, key='test_key')
        
        # Check that the message was sent to the correct topic with the correct data
        self.producer_mock.send.assert_called_once_with('test_topic', value=message_data, key='test_key')
        self.future_mock.get.assert_called_once_with(timeout=10)
        self.assertTrue(result)
    
    @patch('kafka.KafkaProducer')
    def test_kafka_producer_send_message_error(self, mock_kafka_producer):
        """Test handling of errors when sending a message to Kafka."""
        mock_kafka_producer.return_value = self.producer_mock
        self.producer_mock.send.side_effect = Exception('Test error')
        
        producer = ChatKafkaProducer(bootstrap_servers='test:9094', topic='test_topic')
        message_data = {'message': 'test message', 'sender': 'test_user'}
        
        result = producer.send_message(message_data)
        
        # Check that the error was handled and the method returned False
        self.assertFalse(result)
    
    @patch('kafka.KafkaProducer')
    def test_kafka_producer_init_error(self, mock_kafka_producer):
        """Test handling of errors during initialization of the Kafka producer."""
        mock_kafka_producer.side_effect = Exception('Test error')
        
        producer = ChatKafkaProducer(bootstrap_servers='test:9094', topic='test_topic')
        
        # Check that the producer is None when initialization fails
        self.assertIsNone(producer.producer)
    
    @patch('kafka.KafkaProducer')
    def test_kafka_producer_close(self, mock_kafka_producer):
        """Test closing the Kafka producer."""
        mock_kafka_producer.return_value = self.producer_mock
        
        producer = ChatKafkaProducer(bootstrap_servers='test:9094', topic='test_topic')
        producer.close()
        
        # Check that the producer was closed
        self.producer_mock.close.assert_called_once()


@unittest.skip("Skip WebSocket tests that require a running Kafka server")
class WebSocketKafkaIntegrationTests(TestCase):
    """
    Tests for the integration of WebSockets with Kafka.
    
    This class tests the sending of messages via WebSockets and their
    forwarding to Kafka topics. These tests require a running Kafka server
    and are skipped by default.
    """
    
    async def setUp(self):
        """Set up test environment."""
        self.user1 = await database_sync_to_async(User.objects.create_user)(
            username='testuser1', password='testpass1'
        )
        self.user2 = await database_sync_to_async(User.objects.create_user)(
            username='testuser2', password='testpass2'
        )
    
    @patch('chat.kafka_utils.ChatKafkaProducer.send_message_async')
    async def test_new_message_sent_to_kafka(self, mock_send_message_async):
        """Test that new messages are sent to Kafka."""
        mock_send_message_async.return_value = True
        
        # Connect to the WebSocket
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/testuser2/"
        )
        communicator.scope['user'] = self.user1
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Send a message
        await communicator.send_json_to({
            'message': 'Hello, Kafka!',
            'username': 'testuser1',
            'room_name': 'testuser2'
        })
        
        # Wait for the response
        response = await communicator.receive_json_from()
        
        # Check that the message was sent to Kafka
        mock_send_message_async.assert_called_once()
        kafka_message = mock_send_message_async.call_args[1]['message_data']
        self.assertEqual(kafka_message['content'], 'Hello, Kafka!')
        self.assertEqual(kafka_message['sender'], 'testuser1')
        self.assertEqual(kafka_message['receiver'], 'testuser2')
        self.assertEqual(kafka_message['event_type'], 'new_message')
        
        # Close the connection
        await communicator.disconnect()
    
    @patch('chat.kafka_utils.ChatKafkaProducer.send_message_async')
    async def test_update_message_sent_to_kafka(self, mock_send_message_async):
        """Test that message updates are sent to Kafka."""
        mock_send_message_async.return_value = True
        
        # Create a message to update
        message = await database_sync_to_async(Message.objects.create)(
            sender=self.user1, receiver=self.user2, content='Original message'
        )
        
        # Connect to the WebSocket
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/testuser2/"
        )
        communicator.scope['user'] = self.user1
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Update the message
        await communicator.send_json_to({
            'message': 'Updated message',
            'username': 'testuser1',
            'room_name': 'testuser2',
            'message_id': message.id
        })
        
        # Wait for the response
        response = await communicator.receive_json_from()
        
        # Check that the update was sent to Kafka
        mock_send_message_async.assert_called_once()
        kafka_message = mock_send_message_async.call_args[1]['message_data']
        self.assertEqual(kafka_message['content'], 'Updated message')
        self.assertEqual(kafka_message['sender'], 'testuser1')
        self.assertEqual(kafka_message['receiver'], 'testuser2')
        self.assertEqual(kafka_message['message_id'], message.id)
        self.assertEqual(kafka_message['event_type'], 'update_message')
        
        # Close the connection
        await communicator.disconnect()
    
    @patch('chat.kafka_utils.ChatKafkaProducer.send_message_async')
    async def test_delete_message_sent_to_kafka(self, mock_send_message_async):
        """Test that message deletions are sent to Kafka."""
        mock_send_message_async.return_value = True
        
        # Create a message to delete
        message = await database_sync_to_async(Message.objects.create)(
            sender=self.user1, receiver=self.user2, content='Message to delete'
        )
        
        # Connect to the WebSocket
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/testuser2/"
        )
        communicator.scope['user'] = self.user1
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Delete the message
        await communicator.send_json_to({
            'delete_message_id': message.id,
            'username': 'testuser1',
            'room_name': 'testuser2'
        })
        
        # Wait for the response
        response = await communicator.receive_json_from()
        
        # Check that the deletion was sent to Kafka
        mock_send_message_async.assert_called_once()
        kafka_message = mock_send_message_async.call_args[1]['message_data']
        self.assertEqual(kafka_message['message_id'], message.id)
        self.assertEqual(kafka_message['sender'], 'testuser1')
        self.assertEqual(kafka_message['receiver'], 'testuser2')
        self.assertEqual(kafka_message['event_type'], 'delete_message')
        
        # Close the connection
        await communicator.disconnect()
