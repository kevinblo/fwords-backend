from django.db import models


class Language(models.Model):
    """Model to store language information"""
    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Language code (e.g., 'en', 'ru', 'es')"
    )
    name_english = models.CharField(
        max_length=100,
        help_text="Language name in English"
    )
    name_native = models.CharField(
        max_length=100,
        help_text="Language name in its native language"
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Whether this language is enabled and available for use"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name_english} ({self.code})"

    class Meta:
        ordering = ['name_english']
        verbose_name = "Language"
        verbose_name_plural = "Языки для изучения"
