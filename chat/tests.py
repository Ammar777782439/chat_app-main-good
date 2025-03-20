from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from chat.models import Message
from chat.serializers import MessageSerializer
from django.utils import timezone

class MessageViewSetTest(APITestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        
        # Create test messages
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
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

    def test_get_messages(self):
        """Test retrieving messages"""
        response = self.client.get('/api/messages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_filtered_messages(self):
        """Test retrieving messages filtered by user"""
        response = self.client.get(f'/api/messages/?user={self.user2.username}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_create_message(self):
        """Test creating a new message"""
        data = {
            'receiver': self.user2.id,
            'content': 'New test message'
        }
        response = self.client.post('/api/messages/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 3)

    def test_delete_message(self):
        """Test deleting own message"""
        response = self.client.delete(f'/api/messages/{self.message1.id}/delete_message/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Message.objects.count(), 1)

    def test_delete_others_message(self):
        """Test attempting to delete another user's message"""
        response = self.client.delete(f'/api/messages/{self.message2.id}/delete_message/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_message(self):
        """Test updating own message"""
        data = {'content': 'Updated content'}
        response = self.client.post(f'/api/messages/{self.message1.id}/update_message/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.message1.refresh_from_db()
        self.assertEqual(self.message1.content, 'Updated content')

    def test_update_others_message(self):
        """Test attempting to update another user's message"""
        data = {'content': 'Updated content'}
        response = self.client.post(f'/api/messages/{self.message2.id}/update_message/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class ChatRoomViewTest(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        
        # Create test messages
        self.message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content='Hello user2'
        )
        
        # Set up client
        self.client = Client()
        self.client.login(username='user1', password='testpass123')

    def test_chat_room_view(self):
        """Test chat room view with authentication"""
        response = self.client.get(f'/chat/{self.user2.username}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat.html')

    def test_chat_room_view_unauthenticated(self):
        """Test chat room view without authentication"""
        self.client.logout()
        response = self.client.get(f'/chat/{self.user2.username}/')
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_chat_room_search(self):
        """Test chat room search functionality"""
        response = self.client.get(f'/chat/{self.user2.username}/?search=Hello')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat.html')