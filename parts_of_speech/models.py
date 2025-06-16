from django.db import models
from languages.models import Language


class PartOfSpeech(models.Model):
    """
    Основная модель для частей речи.
    Каждая часть речи имеет уникальный код и переводы на разные языки.
    """
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Уникальный код части речи (например: 'noun', 'verb', 'adjective')"
    )
    description = models.TextField(
        blank=True,
        help_text="Описание части речи на английском языке"
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Активна ли данная часть речи"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    def get_translation(self, language_code):
        """Получить перевод части речи для указанного языка"""
        try:
            translation = self.translations.get(language__code=language_code)
            return translation.name.lower()
        except PartOfSpeechTranslation.DoesNotExist:
            return self.code

    def get_abbreviation_translation(self, language_code):
        """Получить перевод сокращенной части речи для указанного языка"""
        try:
            translation = self.translations.get(language__code=language_code)
            return translation.abbreviation.lower()
        except PartOfSpeechTranslation.DoesNotExist:
            return self.code

    def get_all_translations(self):
        """Получить все переводы части речи"""
        return {
            translation.language.code: translation.name 
            for translation in self.translations.all()
        }

    class Meta:
        ordering = ['code']
        verbose_name = "Часть речи"
        verbose_name_plural = "Части речи"


class PartOfSpeechTranslation(models.Model):
    """
    Модель для переводов частей речи на разные языки.
    Связывает часть речи с языком и содержит название на этом языке.
    """
    part_of_speech = models.ForeignKey(
        PartOfSpeech,
        on_delete=models.CASCADE,
        related_name='translations',
        help_text="Часть речи"
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='part_of_speech_translations',
        help_text="Язык перевода"
    )
    name = models.CharField(
        max_length=100,
        help_text="Название части речи на указанном языке"
    )
    abbreviation = models.CharField(
        max_length=10,
        blank=True,
        help_text="Сокращение части речи (например: 'сущ.', 'гл.', 'прил.')"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.part_of_speech.code} - {self.name} ({self.language.code})"

    class Meta:
        unique_together = ['part_of_speech', 'language']
        ordering = ['part_of_speech__code', 'language__code']
        verbose_name = "Перевод части речи"
        verbose_name_plural = "Переводы частей речи"
