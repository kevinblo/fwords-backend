from django.test import TestCase
from django.urls import reverse
from django.core import mail
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import EmailActivationToken

User = get_user_model()


class UserRegistrationTestCase(APITestCase):
    """Test cases for user registration"""

    def setUp(self):
        self.registration_url = reverse('user-register')
        self.valid_user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpassword123',
            'password_confirm': 'testpassword123'
        }

    def test_user_registration_success(self):
        """Test successful user registration"""
        response = self.client.post(self.registration_url, self.valid_user_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

        # Check if activation email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Activate your ForeignWords account', mail.outbox[0].subject)

    def test_user_registration_password_mismatch(self):
        """Test registration with password mismatch"""
        data = self.valid_user_data.copy()
        data['password_confirm'] = 'differentpassword'

        response = self.client.post(self.registration_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        User.objects.create_user(
            email='test@example.com',
            username='existinguser',
            password='password123'
        )

        response = self.client.post(self.registration_url, self.valid_user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EmailActivationTestCase(APITestCase):
    """Test cases for email activation"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='password123',
            is_active=False
        )
        self.activation_token = EmailActivationToken.objects.create(user=self.user)

    def test_email_activation_success(self):
        """Test successful email activation"""
        url = reverse('activate-email', kwargs={'token': self.activation_token.token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh user from database
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)

        # Check token is marked as used
        self.activation_token.refresh_from_db()
        self.assertTrue(self.activation_token.is_used)

    def test_email_activation_invalid_token(self):
        """Test activation with invalid token"""
        url = reverse('activate-email', kwargs={'token': '12345678-1234-1234-1234-123456789012'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTestCase(APITestCase):
    """Test cases for user login"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='password123',
            is_active=True,
            is_email_verified=True
        )
        self.login_url = reverse('user-login')

    def test_user_login_success(self):
        """Test successful user login"""
        data = {
            'email': 'test@example.com',
            'password': 'password123'
        }

        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])

    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }

        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_unverified_email(self):
        """Test login with unverified email"""
        self.user.is_email_verified = False
        self.user.save()

        data = {
            'email': 'test@example.com',
            'password': 'password123'
        }

        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
