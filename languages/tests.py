from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Language

User = get_user_model()


class LanguageModelTest(TestCase):
    """Test cases for Language model"""

    def setUp(self):
        self.language = Language.objects.create(
            code='en',
            name_english='English',
            name_native='English',
            enabled=True
        )

    def test_language_creation(self):
        """Test language creation"""
        self.assertEqual(self.language.code, 'en')
        self.assertEqual(self.language.name_english, 'English')
        self.assertEqual(self.language.name_native, 'English')
        self.assertTrue(self.language.enabled)

    def test_language_default_enabled(self):
        """Test that enabled field defaults to True"""
        language = Language.objects.create(
            code='fr',
            name_english='French',
            name_native='Français'
        )
        self.assertTrue(language.enabled)

    def test_language_str_representation(self):
        """Test string representation"""
        expected = "English (en)"
        self.assertEqual(str(self.language), expected)

    def test_unique_code_constraint(self):
        """Test that language code must be unique"""
        with self.assertRaises(Exception):
            Language.objects.create(
                code='en',
                name_english='English US',
                name_native='English US'
            )


class LanguageAPITest(APITestCase):
    """Test cases for Language API"""

    def setUp(self):
        self.language = Language.objects.create(
            code='en',
            name_english='English',
            name_native='English',
            enabled=True
        )
        self.disabled_language = Language.objects.create(
            code='fr',
            name_english='French',
            name_native='Français',
            enabled=False
        )

        # Create users
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            is_staff=True
        )

    def test_get_languages_list_anonymous(self):
        """Test getting list of languages as anonymous user"""
        url = '/api/v1/languages/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_enabled_languages_only(self):
        """Test getting only enabled languages"""
        url = '/api/v1/languages/enabled/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['code'], 'en')

    def test_get_language_by_code(self):
        """Test getting language by code"""
        url = '/api/v1/languages/en/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'en')
        self.assertTrue(response.data['enabled'])

    def test_create_language_anonymous_forbidden(self):
        """Test that anonymous users cannot create languages"""
        url = '/api/v1/languages/'
        data = {
            'code': 'de',
            'name_english': 'German',
            'name_native': 'Deutsch',
            'enabled': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_language_regular_user_forbidden(self):
        """Test that regular users cannot create languages"""
        self.client.force_authenticate(user=self.regular_user)
        url = '/api/v1/languages/'
        data = {
            'code': 'de',
            'name_english': 'German',
            'name_native': 'Deutsch',
            'enabled': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_language_staff_user_allowed(self):
        """Test that staff users can create languages"""
        self.client.force_authenticate(user=self.staff_user)
        url = '/api/v1/languages/'
        data = {
            'code': 'de',
            'name_english': 'German',
            'name_native': 'Deutsch',
            'enabled': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], 'de')

    def test_update_language_staff_user_allowed(self):
        """Test that staff users can update languages"""
        self.client.force_authenticate(user=self.staff_user)
        url = '/api/v1/languages/en/'
        data = {
            'code': 'en',
            'name_english': 'English Updated',
            'name_native': 'English Updated',
            'enabled': False
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name_english'], 'English Updated')
        self.assertFalse(response.data['enabled'])

    def test_filter_by_enabled(self):
        """Test filtering languages by enabled status"""
        url = '/api/v1/languages/'
        response = self.client.get(url, {'enabled_only': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_language_codes(self):
        """Test getting language codes only"""
        url = '/api/v1/languages/codes/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('en', response.data)
        self.assertIn('fr', response.data)
