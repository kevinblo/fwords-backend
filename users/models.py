import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class CustomUserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password"""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with an email and password"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model with email verification"""
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150, blank=True, help_text="Full name of the user")
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Language preferences
    interface_language = models.ForeignKey(
        'languages.Language',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interface_users',
        help_text="Language for user interface"
    )
    native_language = models.ForeignKey(
        'languages.Language',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='native_users',
        help_text="User's native language"
    )
    active_language = models.ForeignKey(
        'languages.Language',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_users',
        help_text="Currently active language for learning"
    )
    notify = models.BooleanField(
        default=True,
        help_text="Enable notifications"
    )

    # Remove username, first_name and last_name fields
    username = None
    first_name = None
    last_name = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name='Пользователь'
        verbose_name_plural='Пользователи'


class EmailActivationToken(models.Model):
    """Model to store email activation tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activation_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        """Check if token is expired"""
        expiry_time = self.created_at + timedelta(hours=getattr(settings, 'ACTIVATION_TOKEN_EXPIRY_HOURS', 24))
        return timezone.now() > expiry_time

    def __str__(self):
        return f"Activation token for {self.user.email}"

    class Meta:
        ordering = ['-created_at']
        verbose_name='Токен активации аккаунта'
        verbose_name_plural='Токены активации аккаунта'


class LanguageProgress(models.Model):
    """Model to track user's language learning progress"""
    LEVEL_CHOICES = (
        ('A1', 'A1'),
        ('A2', 'A2'),
        ('B1', 'B1'),
        ('B2', 'B2'),
        ('C1', 'C1'),
        ('C2', 'C2'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='language_progress')
    language = models.ForeignKey('languages.Language', on_delete=models.CASCADE)
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, default='A1')
    learned_words = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Percentage of learned words (0.00 to 100.00)")
    learned_words_count = models.PositiveIntegerField(default=0, help_text="Number of learned words")
    learned_phrases = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Percentage of learned phrases (0.00 to 100.00)")
    learned_phrases_count = models.PositiveIntegerField(default=0, help_text="Number of learned phrases")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'language')
        ordering = ['-updated_at']
        verbose_name='Прогресс изучения языка'
        verbose_name_plural='Прогресс изучения языка'

    def __str__(self):
        return f"{self.user.email} - {self.language.name_english} ({self.level})"


class WordsProgress(models.Model):
    """Model to track user's progress with individual words"""
    STATUS_CHOICES = (
        ('new', 'Новое'),
        ('learning', 'Изучается'),
        ('learned', 'Изучено'),
        ('mastered', 'Освоено'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='words_progress')
    word = models.ForeignKey('words.Word', on_delete=models.CASCADE, related_name='user_progress')
    target_language = models.ForeignKey(
        'languages.Language', 
        on_delete=models.CASCADE, 
        related_name='words_progress_target',
        help_text='Язык, который изучается'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')
    interval = models.PositiveIntegerField(default=1, help_text='Интервал повторения в днях')
    next_review = models.DateTimeField(null=True, blank=True, help_text='Дата следующего повторения')
    review_count = models.PositiveIntegerField(default=0, help_text='Количество повторений')
    correct_count = models.PositiveIntegerField(default=0, help_text='Количество правильных ответов')
    date_learned = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'word', 'target_language')
        ordering = ['-updated_at']
        verbose_name='Прогресс изучения слов'
        verbose_name_plural='Прогресс изучения слов'

    def __str__(self):
        return f"{self.user.email} - {self.word.word} -> {self.target_language.code} ({self.status})"


class QuizProgress(models.Model):
    """Model to track user's quiz progress"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_progress')
    language = models.ForeignKey(
        'languages.Language', 
        on_delete=models.CASCADE, 
        related_name='quiz_progress',
        help_text='Язык викторины'
    )
    total_questions = models.PositiveIntegerField(help_text='Общее количество вопросов в викторине')
    correct_answers = models.PositiveIntegerField(help_text='Количество правильных ответов')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Прогресс викторины'
        verbose_name_plural = 'Прогресс викторин'

    def __str__(self):
        return f"{self.user.email} - {self.language.name_english} ({self.correct_answers}/{self.total_questions})"

    @property
    def accuracy_percentage(self):
        """Вычисляет процент правильных ответов"""
        if self.total_questions == 0:
            return 0.0
        return round((self.correct_answers / self.total_questions) * 100, 2)
