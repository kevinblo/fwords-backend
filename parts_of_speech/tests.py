from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from languages.models import Language
from .models import PartOfSpeech, PartOfSpeechTranslation


class PartOfSpeechModelTest(TestCase):
    """Тесты для модели PartOfSpeech"""
    
    def setUp(self):
        self.part_of_speech = PartOfSpeech.objects.create(
            code='noun',
            description='A word used to identify any of a class of people, places, or things'
        )
        
        # Создаем языки для тестирования
        self.english = Language.objects.create(
            code='en',
            name_english='English',
            name_native='English'
        )
        self.russian = Language.objects.create(
            code='ru',
            name_english='Russian',
            name_native='Русский'
        )
        
        # Создаем переводы
        PartOfSpeechTranslation.objects.create(
            part_of_speech=self.part_of_speech,
            language=self.english,
            name='Noun',
            abbreviation='n.'
        )
        PartOfSpeechTranslation.objects.create(
            part_of_speech=self.part_of_speech,
            language=self.russian,
            name='Существительное',
            abbreviation='сущ.'
        )
    
    def test_part_of_speech_creation(self):
        """Тест создания части речи"""
        self.assertEqual(self.part_of_speech.code, 'noun')
        self.assertTrue(self.part_of_speech.enabled)
        self.assertIsNotNone(self.part_of_speech.created_at)
    
    def test_get_translation(self):
        """Тест получения перевода части речи"""
        english_translation = self.part_of_speech.get_translation('en')
        russian_translation = self.part_of_speech.get_translation('ru')
        
        self.assertEqual(english_translation, 'Noun')
        self.assertEqual(russian_translation, 'Существительное')
    
    def test_get_translation_nonexistent(self):
        """Тест получения перевода для несуществующего языка"""
        translation = self.part_of_speech.get_translation('fr')
        self.assertEqual(translation, 'noun')  # Возвращает код
    
    def test_get_all_translations(self):
        """Тест получения всех переводов"""
        translations = self.part_of_speech.get_all_translations()
        expected = {
            'en': 'Noun',
            'ru': 'Существительное'
        }
        self.assertEqual(translations, expected)
    
    def test_str_representation(self):
        """Тест строкового представления"""
        self.assertEqual(str(self.part_of_speech), 'noun')


class PartOfSpeechTranslationModelTest(TestCase):
    """Тесты для модели PartOfSpeechTranslation"""
    
    def setUp(self):
        self.part_of_speech = PartOfSpeech.objects.create(
            code='verb',
            description='A word used to describe an action, state, or occurrence'
        )
        self.language = Language.objects.create(
            code='en',
            name_english='English',
            name_native='English'
        )
        self.translation = PartOfSpeechTranslation.objects.create(
            part_of_speech=self.part_of_speech,
            language=self.language,
            name='Verb',
            abbreviation='v.'
        )
    
    def test_translation_creation(self):
        """Тест создания перевода"""
        self.assertEqual(self.translation.name, 'Verb')
        self.assertEqual(self.translation.abbreviation, 'v.')
        self.assertIsNotNone(self.translation.created_at)
    
    def test_unique_constraint(self):
        """Тест уникальности комбинации часть речи + язык"""
        with self.assertRaises(Exception):
            PartOfSpeechTranslation.objects.create(
                part_of_speech=self.part_of_speech,
                language=self.language,
                name='Another Verb',
                abbreviation='verb'
            )
    
    def test_str_representation(self):
        """Тест строкового представления"""
        expected = f"{self.part_of_speech.code} - {self.translation.name} ({self.language.code})"
        self.assertEqual(str(self.translation), expected)


class PartOfSpeechAPITest(APITestCase):
    """Тесты для API частей речи"""
    
    def setUp(self):
        # Создаем языки
        self.english = Language.objects.create(
            code='en',
            name_english='English',
            name_native='English'
        )
        self.russian = Language.objects.create(
            code='ru',
            name_english='Russian',
            name_native='Русский'
        )
        
        # Создаем часть речи
        self.part_of_speech = PartOfSpeech.objects.create(
            code='adjective',
            description='A word naming an attribute of a noun'
        )
        
        # Создаем переводы
        PartOfSpeechTranslation.objects.create(
            part_of_speech=self.part_of_speech,
            language=self.english,
            name='Adjective',
            abbreviation='adj.'
        )
    
    def test_list_parts_of_speech(self):
        """Тест получения списка частей речи"""
        url = reverse('partsofspeech-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['code'], 'adjective')
    
    def test_create_part_of_speech(self):
        """Тест создания части речи"""
        url = reverse('partsofspeech-list')
        data = {
            'code': 'adverb',
            'description': 'A word that modifies a verb, adjective, or other adverb',
            'enabled': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], 'adverb')
        self.assertTrue(PartOfSpeech.objects.filter(code='adverb').exists())
    
    def test_get_part_of_speech_detail(self):
        """Тест получения детальной информации о части речи"""
        url = reverse('partsofspeech-detail', kwargs={'pk': self.part_of_speech.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'adjective')
        self.assertIn('translations', response.data)
        self.assertIn('translations_dict', response.data)
    
    def test_get_enabled_parts_of_speech(self):
        """Тест получения только активных частей речи"""
        # Создаем неактивную часть речи
        PartOfSpeech.objects.create(
            code='disabled',
            description='Disabled part of speech',
            enabled=False
        )
        
        url = reverse('partsofspeech-enabled')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Должна быть только одна активная часть речи
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['code'], 'adjective')
    
    def test_get_simple_parts_of_speech(self):
        """Тест получения упрощенного списка частей речи"""
        url = reverse('partsofspeech-simple')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        # Проверяем, что возвращаются только нужные поля
        expected_fields = {'id', 'code', 'name'}
        actual_fields = set(response.data[0].keys())
        self.assertEqual(actual_fields, expected_fields)
