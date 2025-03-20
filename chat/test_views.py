"""Tests for views in the chat application.

This module contains tests for the views and API endpoints in the chat application.
It tests the chat room view, message API endpoints, and other view functionality.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from chat.models import Message
from django.db.models import Q
import json


class ChatViewsDetailedTest(TestCase):
    """Detailed test cases for chat views."""

    def setUp(self):
        """Set up test data."""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpassword1'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpassword2'
        )
        self.user3 = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpassword3'
        )

        # Create test messages
        self.message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Test message 1'
        )
        self.message2 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content='Test message 2'
        )
        self.message3 = Message.objects.create(
            sender=self.user1,
            receiver=self.user3,
            content='Test message 3'
        )

        # Create clients
        self.client = Client()
        self.api_client = APIClient()

    def test_chat_room_with_search(self):
        """Test chat room view with search parameter."""
        # Login
        self.client.login(username='testuser1', password='testpassword1')

        # Access chat room with search parameter
        url = reverse('chat', args=['testuser2']) + '?search=message'
        response = self.client.get(url)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat.html')
        self.assertContains(response, 'Test message')

    def test_message_viewset_list_filter_by_user(self):
        """Test filtering messages by user in the API."""
        # Login
        self.api_client.force_authenticate(user=self.user1)

        # Get messages filtered by user
        url = reverse('message-list') + '?user=testuser2'
        response = self.api_client.get(url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 2)  # Only messages between user1 and user2

    def test_message_viewset_create(self):
        """Test creating a message through the API."""
        # Login
        self.api_client.force_authenticate(user=self.user1)

        # Create a new message
        url = reverse('message-list')
        data = {
            'receiver': self.user2.id,
            'content': 'New test message'
        }
        response = self.api_client.post(url, data, format='json')

        # Check response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'New test message')
        self.assertEqual(response.data['sender'], self.user1.id)
        self.assertEqual(response.data['receiver'], self.user2.id)

    def test_message_viewset_retrieve(self):
        """Test retrieving a specific message through the API."""
        # Login
        self.api_client.force_authenticate(user=self.user1)

        # Retrieve a message
        url = reverse('message-detail', args=[self.message1.id])
        response = self.api_client.get(url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.message1.id)
        self.assertEqual(response.data['content'], 'Test message 1')

    def test_update_message_own_message(self):
        """Test updating own message through the API."""
        # Login
        self.api_client.force_authenticate(user=self.user1)

        # Update a message
        url = reverse('message-update-message', args=[self.message1.id])
        data = {'content': 'Updated message content'}
        response = self.api_client.post(url, data, format='json')

        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Updated message content')

        # Check that the message was updated in the database
        updated_message = Message.objects.get(id=self.message1.id)
        self.assertEqual(updated_message.content, 'Updated message content')

    def test_update_message_other_user_message(self):
        """Test that a user cannot update another user's message."""
        # Login as user3
        self.api_client.force_authenticate(user=self.user3)

        # Try to update user1's message
        url = reverse('message-update-message', args=[self.message1.id])
        data = {'content': 'Unauthorized update'}
        response = self.api_client.post(url, data, format='json')

        # Check response
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Check that the message was not updated
        unchanged_message = Message.objects.get(id=self.message1.id)
        self.assertEqual(unchanged_message.content, 'Test message 1')

    def test_update_message_empty_content(self):
        """Test that a message cannot be updated with empty content."""
        # Login
        self.api_client.force_authenticate(user=self.user1)

        # Try to update with empty content
        url = reverse('message-update-message', args=[self.message1.id])
        data = {'content': ''}
        response = self.api_client.post(url, data, format='json')

        # Check response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check that the message was not updated
        unchanged_message = Message.objects.get(id=self.message1.id)
        self.assertEqual(unchanged_message.content, 'Test message 1')

    def test_delete_message_own_message(self):
        """Test deleting own message through the API."""
        # Login
        self.api_client.force_authenticate(user=self.user1)

        # Delete a message
        url = reverse('message-delete-message', args=[self.message1.id])
        response = self.api_client.delete(url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check that the message was deleted from the database
        with self.assertRaises(Message.DoesNotExist):
            Message.objects.get(id=self.message1.id)

    def test_delete_message_other_user_message(self):
        """Test that a user cannot delete another user's message."""
        # Login as user3
        self.api_client.force_authenticate(user=self.user3)

        # Try to delete user1's message
        url = reverse('message-delete-message', args=[self.message1.id])
        response = self.api_client.delete(url)

        # Check response
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Check that the message was not deleted
        self.assertTrue(Message.objects.filter(id=self.message1.id).exists())
