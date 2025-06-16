from django.db import models
from languages.models import Language
from parts_of_speech.models import PartOfSpeech


class Gender(models.TextChoices):
    """Выбор рода для слов"""
    MASCULINE = 'masculine', 'Мужской'
    FEMININE = 'feminine', 'Женский'
    NEUTER = 'neuter', 'Средний'
    COMMON = 'common', 'Общий'


class DifficultyLevel(models.TextChoices):
    """Уровень сложности слова"""
    BEGINNER = 'beginner', 'A1'
    ELEMENTARY = 'elementary', 'A2'
    INTERMEDIATE = 'intermediate', 'B1'
    UPPER_INTERMEDIATE = 'upper_intermediate', 'B2'
    ADVANCED = 'advanced', 'C1'
    PROFICIENT = 'proficient', 'C2'


class Word(models.Model):
    """
    Основная модель для слов.
    Каждое слово имеет уникальную комбинацию слово+язык и переводы на другие языки.
    """
    word = models.CharField(
        max_length=200,
        help_text="Само слово"
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='words',
        help_text="Язык слова"
    )
    transcription = models.CharField(
        max_length=300,
        blank=True,
        help_text="Транскрипция слова"
    )
    part_of_speech = models.ForeignKey(
        PartOfSpeech,
        on_delete=models.CASCADE,
        related_name='words',
        help_text="Часть речи"
    )
    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        blank=True,
        null=True,
        help_text="Род слова (необязательно)"
    )
    difficulty_level = models.CharField(
        max_length=30,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.BEGINNER,
        help_text="Уровень сложности слова"
    )
    audio_url = models.CharField(
        max_length=255,
        blank=True,
        help_text="URL аудиофайла с произношением"
    )
    active = models.BooleanField(
        default=True,
        help_text="Активно ли слово"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.word} ({self.language.code})"

    def get_translations(self):
        """Получить все переводы слова"""
        return WordTranslation.objects.filter(
            models.Q(source_word=self) | models.Q(target_word=self)
        ).select_related('source_word__language', 'target_word__language')

    def get_translations_to_language(self, language_code):
        """Получить переводы слова на указанный язык"""
        return WordTranslation.objects.filter(
            source_word=self,
            target_word__language__code=language_code
        ).select_related('target_word')

    def get_translations_from_language(self, language_code):
        """Получить переводы с указанного языка на это слово"""
        return WordTranslation.objects.filter(
            target_word=self,
            source_word__language__code=language_code
        ).select_related('source_word')
    
    def get_all_translations_dict(self):
        """Получить все переводы в виде словаря {язык: [слова]}"""
        translations_dict = {}
        
        # Получаем переводы, где это слово является источником
        for translation in self.translations_as_source.select_related('target_word__language'):
            lang_code = translation.target_word.language.code
            if lang_code not in translations_dict:
                translations_dict[lang_code] = []
            translations_dict[lang_code].append({
                'word': translation.target_word.word,
                'id': translation.target_word.id,
                'confidence': translation.confidence,
                'notes': translation.notes
            })
        
        # Получаем переводы, где это слово является целью
        for translation in self.translations_as_target.select_related('source_word__language'):
            lang_code = translation.source_word.language.code
            if lang_code not in translations_dict:
                translations_dict[lang_code] = []
            translations_dict[lang_code].append({
                'word': translation.source_word.word,
                'id': translation.source_word.id,
                'confidence': translation.confidence,
                'notes': translation.notes
            })
        
        return translations_dict

    class Meta:
        unique_together = ['word', 'language']
        ordering = ['word']
        verbose_name = "Слово"
        verbose_name_plural = "Слова"
        indexes = [
            models.Index(fields=['word']),
            models.Index(fields=['language']),
            models.Index(fields=['part_of_speech']),
            models.Index(fields=['active']),
            models.Index(fields=['difficulty_level']),
        ]


class WordTranslation(models.Model):
    """
    Модель для переводов слов между языками.
    Связывает слово на одном языке со словом на другом языке.
    """
    source_word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name='translations_as_source',
        help_text="Исходное слово"
    )
    target_word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name='translations_as_target',
        help_text="Целевое слово (перевод)"
    )
    confidence = models.FloatField(
        default=1.0,
        help_text="Уверенность в переводе (0.0 - 1.0)"
    )
    notes = models.TextField(
        blank=True,
        help_text="Дополнительные заметки о переводе"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.source_word.word} ({self.source_word.language.code}) → {self.target_word.word} ({self.target_word.language.code})"

    def clean(self):
        """Валидация модели"""
        from django.core.exceptions import ValidationError
        
        if self.source_word and self.target_word:
            if self.source_word.language == self.target_word.language:
                raise ValidationError("Исходное и целевое слово не могут быть на одном языке")
            
            if self.source_word == self.target_word:
                raise ValidationError("Исходное и целевое слово не могут быть одинаковыми")

    def save(self, *args, **kwargs):
        """Сохранение с автоматическим созданием обратного перевода"""
        # Флаг для предотвращения бесконечной рекурсии
        create_reverse = kwargs.pop("create_reverse", True)
        
        # Сначала сохраняем текущий перевод
        super().save(*args, **kwargs)
        
        # Создаем обратный перевод, если его нет и если это разрешено
        if create_reverse:
            reverse_translation_exists = WordTranslation.objects.filter(
                source_word=self.target_word,
                target_word=self.source_word
            ).exists()
            
            if not reverse_translation_exists:
                # Создаем объект обратного перевода
                reverse_translation = WordTranslation(
                    source_word=self.target_word,
                    target_word=self.source_word,
                    confidence=self.confidence,
                    notes=self.notes
                )
                # Сохраняем с флагом предотвращения рекурсии
                reverse_translation.save(create_reverse=False)

    class Meta:
        unique_together = ['source_word', 'target_word']
        ordering = ['source_word__word', 'target_word__word']
        verbose_name = "Перевод слова"
        verbose_name_plural = "Переводы слов"
        indexes = [
            models.Index(fields=['source_word']),
            models.Index(fields=['target_word']),
            models.Index(fields=['confidence']),
        ]


class WordExample(models.Model):
    """
    Модель для примеров использования слов.
    Содержит предложения с использованием слова и их переводы.
    """
    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name='examples',
        help_text="Слово, для которого приводится пример"
    )
    example_text = models.TextField(
        help_text="Пример предложения с использованием слова"
    )
    translation = models.TextField(
        blank=True,
        help_text="Перевод примера"
    )
    translation_language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='word_example_translations',
        null=True,
        blank=True,
        help_text="Язык перевода примера"
    )
    audio_url = models.URLField(
        blank=True,
        help_text="URL аудиофайла с произношением примера"
    )
    active = models.BooleanField(
        default=True,
        help_text="Активен ли пример"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Пример для '{self.word.word}': {self.example_text[:50]}..."

    class Meta:
        ordering = ['word', 'created_at']
        verbose_name = "Пример использования слова"
        verbose_name_plural = "Примеры использования слов"
        indexes = [
            models.Index(fields=['word']),
            models.Index(fields=['active']),
        ]
