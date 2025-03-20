from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from rest_framework.test import APIClient
from rest_framework import status

class UserViewsTest(TestCase):
    def setUp(self):
        # Create test users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )

        # Create client
        self.client = Client()

    def test_login_page_get(self):
        """Test the login page loads correctly"""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_page_post_valid(self):
        """Test login with valid credentials"""
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        self.assertRedirects(response, '/chat/Ammar/')

    def test_login_page_post_invalid(self):
        """Test login with invalid credentials"""
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page
        messages = list(get_messages(response.wsgi_request))
        self.assertGreater(len(messages), 0)
        self.assertIn('Invalid', str(messages[0]))

    def test_login_page_authenticated_user(self):
        """Test that authenticated users are redirected from login page"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/chat/Ammar/')

    def test_home_view_authenticated(self):
        """Test home view with authenticated user"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/chat/Ammar/')

    def test_home_view_unauthenticated(self):
        """Test home view with unauthenticated user"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/')

    def test_signup_view_get(self):
        """Test the signup page loads correctly"""
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_signup_view_post_valid(self):
        """Test signup with valid data"""
        response = self.client.post('/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newpassword123',
            'password2': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after signup
        # Check user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_signup_view_post_password_mismatch(self):
        """Test signup with mismatched passwords"""
        response = self.client.post('/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'password123',
            'password2': 'differentpassword',
        })
        self.assertEqual(response.status_code, 200)  # Stay on signup page
        # Check user was not created
        self.assertFalse(User.objects.filter(username='newuser').exists())
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertGreater(len(messages), 0)
        self.assertIn('Passwords do not match', str(messages[0]))

    def test_signup_view_authenticated_user(self):
        """Test that authenticated users are redirected from signup page"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/chat/Ammar/')

    def test_signup_view_post_existing_username(self):
        """Test signup with an existing username"""
        response = self.client.post('/register/', {
            'username': 'testuser',  # This username already exists
            'email': 'another@example.com',
            'password1': 'password123',
            'password2': 'password123',
        })
        self.assertEqual(response.status_code, 200)  # Stay on signup page
        messages = list(get_messages(response.wsgi_request))
        self.assertGreater(len(messages), 0)
        # The error message comes from the database constraint
        self.assertIn('duplicate key value', str(messages[0]))

    def test_logout_view(self):
        """Test logout functionality"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post('/logout/')  # Using POST instead of GET
        self.assertEqual(response.status_code, 302)  # Redirect after logout
        self.assertRedirects(response, '/login/')
        # Check user is logged out
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_get_auth_token(self):
        """Test getting authentication token"""
        # Set up API client
        api_client = APIClient()
        api_client.force_authenticate(user=self.user)
        
        response = api_client.get('/api/token/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)