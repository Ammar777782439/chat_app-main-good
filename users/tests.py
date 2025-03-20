from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages

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

    def test_logout_page(self):
        """Test logout functionality"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, 302)  # Redirect after logout
        # Check user is logged out
        self.assertFalse('_auth_user_id' in self.client.session)

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

    def test_login_view_get(self):
        """Test the login view loads correctly"""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_view_post_valid(self):
        """Test login view with valid credentials"""
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        self.assertRedirects(response, '/chat/Ammar/')

    def test_login_view_post_invalid(self):
        """Test login view with invalid credentials"""
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page
        messages = list(get_messages(response.wsgi_request))
        self.assertGreater(len(messages), 0)
        self.assertIn('Invalid', str(messages[0]))

    def test_register_view_get(self):
        """Test the register view loads correctly"""
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_register_view_post_valid(self):
        """Test register view with valid data"""
        response = self.client.post('/register/', {
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'password1': 'newpassword123',
            'password2': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after signup
        # Check user was created
        self.assertTrue(User.objects.filter(username='newuser2').exists())

    def test_custom_logout(self):
        """Test custom logout functionality"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, 302)  # Redirect after logout
        # Check user is logged out
        self.assertFalse('_auth_user_id' in self.client.session)
