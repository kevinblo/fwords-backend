from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.exceptions import ValidationError
from languages.models import Language
from parts_of_speech.models import PartOfSpeech
from .models import Word, WordTranslation, WordExample, Gender


class WordModelTest(TestCase):
    """Тесты для модели Word"""
    
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
        self.noun = PartOfSpeech.objects.create(
            code='noun',
            description='A word used to identify any of a class of people, places, or things'
        )
        
        # Создаем слово
        self.word = Word.objects.create(
            word='house',
            language=self.english,
            transcription='/haʊs/',
            part_of_speech=self.noun,
            gender=Gender.NEUTER,
            audio_url='https://example.com/house.mp3'
        )
    
    def test_word_creation(self):
        """Тест создания слова"""
        self.assertEqual(self.word.word, 'house')
        self.assertEqual(self.word.language, self.english)
        self.assertEqual(self.word.transcription, '/haʊs/')
        self.assertEqual(self.word.part_of_speech, self.noun)
        self.assertEqual(self.word.gender, Gender.NEUTER)
        self.assertTrue(self.word.active)
        self.assertIsNotNone(self.word.created_at)
    
    def test_word_str_representation(self):
        """Тест строкового представления слова"""
        expected = f"{self.word.word} ({self.word.language.code})"
        self.assertEqual(str(self.word), expected)
    
    def test_unique_word_language_constraint(self):
        """Тест уникальности комбинации слово+язык"""
        with self.assertRaises(Exception):
            Word.objects.create(
                word='house',
                language=self.english,
                part_of_speech=self.noun
            )
    
    def test_word_translations_methods(self):
        """Тест методов получения переводов"""
        # Создаем русское слово
        russian_word = Word.objects.create(
            word='дом',
            language=self.russian,
            part_of_speech=self.noun,
            gender=Gender.MASCULINE
        )
        
        # Создаем перевод
        translation = WordTranslation.objects.create(
            source_word=self.word,
            target_word=russian_word,
            confidence=0.9
        )
        
        # Тестируем методы
        translations = self.word.get_translations()
        self.assertEqual(translations.count(), 1)
        
        translations_to_ru = self.word.get_translations_to_language('ru')
        self.assertEqual(translations_to_ru.count(), 1)
        
        translations_from_en = russian_word.get_translations_from_language('en')
        self.assertEqual(translations_from_en.count(), 1)


class WordTranslationModelTest(TestCase):
    """Тесты для модели WordTranslation"""
    
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
        self.noun = PartOfSpeech.objects.create(
            code='noun',
            description='A word used to identify any of a class of people, places, or things'
        )
        
        # Создаем слова
        self.english_word = Word.objects.create(
            word='cat',
            language=self.english,
            part_of_speech=self.noun
        )
        self.russian_word = Word.objects.create(
            word='кот',
            language=self.russian,
            part_of_speech=self.noun,
            gender=Gender.MASCULINE
        )
        
        # Создаем перевод
        self.translation = WordTranslation.objects.create(
            source_word=self.english_word,
            target_word=self.russian_word,
            confidence=0.95,
            notes='Common translation'
        )
    
    def test_translation_creation(self):
        """Тест создания перевода"""
        self.assertEqual(self.translation.source_word, self.english_word)
        self.assertEqual(self.translation.target_word, self.russian_word)
        self.assertEqual(self.translation.confidence, 0.95)
        self.assertEqual(self.translation.notes, 'Common translation')
        self.assertIsNotNone(self.translation.created_at)
    
    def test_translation_str_representation(self):
        """Тест строкового представления перевода"""
        expected = f"{self.english_word.word} ({self.english_word.language.code}) → {self.russian_word.word} ({self.russian_word.language.code})"
        self.assertEqual(str(self.translation), expected)
    
    def test_unique_translation_constraint(self):
        """Тест уникальности перевода"""
        with self.assertRaises(Exception):
            WordTranslation.objects.create(
                source_word=self.english_word,
                target_word=self.russian_word,
                confidence=0.8
            )
    
    def test_translation_validation(self):
        """Тест валидации перевода"""
        # Тест перевода на тот же язык
        english_word2 = Word.objects.create(
            word='dog',
            language=self.english,
            part_of_speech=self.noun
        )
        
        translation = WordTranslation(
            source_word=self.english_word,
            target_word=english_word2
        )
        
        with self.assertRaises(ValidationError):
            translation.clean()


class WordExampleModelTest(TestCase):
    """Тесты для модели WordExample"""
    
    def setUp(self):
        # Создаем язык и часть речи
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
        
        self.verb = PartOfSpeech.objects.create(
            code='verb',
            description='A word used to describe an action, state, or occurrence'
        )
        
        # Создаем слово
        self.word = Word.objects.create(
            word='run',
            language=self.english,
            part_of_speech=self.verb
        )
        
        # Создаем пример
        self.example = WordExample.objects.create(
            word=self.word,
            example_text='I run every morning.',
            translation='Я бегаю каждое утро.',
            translation_language=self.russian,
            audio_url='https://example.com/run_example.mp3'
        )
    
    def test_example_creation(self):
        """Тест создания примера"""
        self.assertEqual(self.example.word, self.word)
        self.assertEqual(self.example.example_text, 'I run every morning.')
        self.assertEqual(self.example.translation, 'Я бегаю каждое утро.')
        self.assertEqual(self.example.translation_language, self.russian)
        self.assertTrue(self.example.active)
        self.assertIsNotNone(self.example.created_at)
    
    def test_example_str_representation(self):
        """Тест строкового представления примера"""
        expected = f"Пример для '{self.word.word}': {self.example.example_text[:50]}..."
        self.assertEqual(str(self.example), expected)


class WordAPITest(APITestCase):
    """Тесты для API слов"""
    
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
        self.noun = PartOfSpeech.objects.create(
            code='noun',
            description='A word used to identify any of a class of people, places, or things'
        )
        
        # Создаем слово
        self.word = Word.objects.create(
            word='book',
            language=self.english,
            transcription='/bʊk/',
            part_of_speech=self.noun,
            audio_url='https://example.com/book.mp3'
        )
    
    def test_list_words(self):
        """Тест получения списка слов"""
        url = reverse('word-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['word'], 'book')
    
    def test_create_word(self):
        """Тест создания слова"""
        url = reverse('word-list')
        data = {
            'word': 'table',
            'language_id': self.english.id,
            'transcription': '/ˈteɪbəl/',
            'part_of_speech_id': self.noun.id,
            'active': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['word'], 'table')
        self.assertTrue(Word.objects.filter(word='table').exists())
    
    def test_get_word_detail(self):
        """Тест получения детальной информации о слове"""
        url = reverse('word-detail', kwargs={'pk': self.word.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['word'], 'book')
        self.assertIn('language', response.data)
        self.assertIn('part_of_speech', response.data)
    
    def test_get_active_words(self):
        """Тест получения только активных слов"""
        # Создаем неактивное слово
        Word.objects.create(
            word='inactive',
            language=self.english,
            part_of_speech=self.noun,
            active=False
        )
        
        url = reverse('word-active')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Должно быть только одно активное слово
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['word'], 'book')
    
    def test_word_search(self):
        """Тест поиска слов"""
        url = reverse('word-search')
        data = {
            'query': 'book',
            'language': 'en',
            'active_only': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['word'], 'book')
    
    def test_word_stats(self):
        """Тест получения статистики слов"""
        url = reverse('word-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_words', response.data)
        self.assertIn('active_words', response.data)
        self.assertIn('words_by_language', response.data)
        self.assertIn('words_by_part_of_speech', response.data)
        self.assertEqual(response.data['total_words'], 1)
        self.assertEqual(response.data['active_words'], 1)
