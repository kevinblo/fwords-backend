from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Q, Count
from django.utils import timezone
from .models import WordsProgress, LanguageProgress
from words.models import Word, DifficultyLevel
import logging

logger = logging.getLogger(__name__)

# Mapping difficulty levels to language levels
DIFFICULTY_TO_LEVEL_MAP = {
    'A1': [DifficultyLevel.BEGINNER],
    'A2': [DifficultyLevel.BEGINNER, DifficultyLevel.ELEMENTARY],
    'B1': [DifficultyLevel.BEGINNER, DifficultyLevel.ELEMENTARY, DifficultyLevel.INTERMEDIATE],
    'B2': [DifficultyLevel.BEGINNER, DifficultyLevel.ELEMENTARY, DifficultyLevel.INTERMEDIATE, DifficultyLevel.UPPER_INTERMEDIATE],
    'C1': [DifficultyLevel.BEGINNER, DifficultyLevel.ELEMENTARY, DifficultyLevel.INTERMEDIATE, DifficultyLevel.UPPER_INTERMEDIATE, DifficultyLevel.ADVANCED],
    'C2': [DifficultyLevel.BEGINNER, DifficultyLevel.ELEMENTARY, DifficultyLevel.INTERMEDIATE, DifficultyLevel.UPPER_INTERMEDIATE, DifficultyLevel.ADVANCED, DifficultyLevel.PROFICIENT],
}


def update_language_progress(user, target_language):
    """
    Update language progress statistics for a user and target language
    """
    try:
        # Get or create LanguageProgress for the user and target language
        language_progress, created = LanguageProgress.objects.get_or_create(
            user=user,
            language=target_language,
            defaults={'level': 'A1'}
        )

        # Get user's current level for this language
        current_level = language_progress.level

        # Get difficulty levels available for current language level
        available_difficulty_levels = DIFFICULTY_TO_LEVEL_MAP.get(current_level, [DifficultyLevel.BEGINNER])

        # Count total words available for learning at current level
        total_available_words = Word.objects.filter(
            language=target_language,
            difficulty_level__in=available_difficulty_levels,
            active=True
        ).count()

        # Count learned and mastered words for this user and language
        learned_mastered_count = WordsProgress.objects.filter(
            user=user,
            target_language=target_language,
            status__in=['learned', 'mastered']
        ).count()

        # Log progress update for debugging
        logger.debug(
            f"Language progress update: User {user.id}, Language {target_language.code}, "
            f"Learned: {learned_mastered_count}/{total_available_words}, Level: {current_level}"
        )

        # Calculate percentage of learned words
        if total_available_words > 0:
            learned_percentage = min(100.0, round((learned_mastered_count / total_available_words) * 100, 2))
        else:
            learned_percentage = 0.0

        # Update the language progress with flag to prevent recursion
        language_progress.learned_words_count = learned_mastered_count
        language_progress.learned_words = learned_percentage
        language_progress._updating_from_signal = True
        language_progress.save(update_fields=['learned_words', 'learned_words_count', 'updated_at'])

        logger.info(
            f"Updated language progress for user {user.username} ({user.id}) "
            f"in {target_language.name_english}: {learned_percentage}% "
            f"({learned_mastered_count}/{total_available_words} words)"
        )

    except Exception as e:
        logger.error(
            f"Failed to update language progress for user {user.id}, "
            f"language {target_language.code}: {str(e)}"
        )


@receiver(post_save, sender=WordsProgress)
def words_progress_updated(sender, instance, created, **kwargs):
    """
    Signal handler for when WordsProgress is created or updated
    """
    try:
        # Only update language progress if the instance has required fields
        if instance.user and instance.target_language:
            update_language_progress(instance.user, instance.target_language)
        else:
            logger.warning(
                f"WordsProgress instance {instance.id} missing user or target_language"
            )
    except Exception as e:
        logger.error(
            f"Error in words_progress_updated signal for instance {instance.id}: {str(e)}"
        )


@receiver(post_delete, sender=WordsProgress)
def words_progress_deleted(sender, instance, **kwargs):
    """
    Signal handler for when WordsProgress is deleted
    """
    try:
        # Only update language progress if the instance has required fields
        if instance.user and instance.target_language:
            update_language_progress(instance.user, instance.target_language)
        else:
            logger.warning(
                f"Deleted WordsProgress instance missing user or target_language"
            )
    except Exception as e:
        logger.error(
            f"Error in words_progress_deleted signal: {str(e)}"
        )


@receiver(post_save, sender=LanguageProgress)
def language_progress_level_updated(sender, instance, created, **kwargs):
    """
    Signal handler for when LanguageProgress level is updated
    Recalculate learned words percentage when level changes
    """
    try:
        # Skip if this update was triggered by our own signal to prevent recursion
        if getattr(instance, '_updating_from_signal', False):
            return

        if not created:
            # Always recalculate when LanguageProgress is updated
            # since we can't easily track field changes without django-model-utils
            update_language_progress(instance.user, instance.language)

    except Exception as e:
        logger.error(
            f"Error in language_progress_level_updated signal for instance {instance.id}: {str(e)}"
        )


@receiver(pre_save, sender=WordsProgress)
def set_date_learned(sender, instance, **kwargs):
    """
    Automatically set date_learned when status changes to 'learned' or 'mastered'
    """
    try:
        # Если это новая запись
        if not instance.pk:
            instance.date_learned = timezone.now().date()
            logger.debug(
                f"Setting date_learned for new word progress: "
                f"Word '{instance.word.word}' (ID: {instance.word.id}) "
                f"to {instance.date_learned}"
            )
            return

        # Если это обновление существующей записи
        try:
            old_instance = WordsProgress.objects.get(pk=instance.pk)

            instance.date_learned = timezone.now().date()
            logger.info(
                f"Auto-setting date_learned for word '{instance.word.word}' "
                f"(ID: {instance.id}) to {instance.date_learned}. "
                f"Status changed from '{old_instance.status}' to '{instance.status}'"
            )

        except WordsProgress.DoesNotExist:
            # Если по какой-то причине старая запись не найдена, просто устанавливаем дату
            instance.date_learned = timezone.now().date()
            logger.warning(
                f"Old WordsProgress instance not found for ID {instance.pk}, "
                f"setting date_learned to {instance.date_learned}"
            )

    except Exception as e:
        logger.error(
            f"Error in set_date_learned signal for WordsProgress {instance.pk}: {str(e)}"
        )


# Additional signal to handle bulk updates more efficiently
@receiver(post_save, sender=WordsProgress)
def log_word_milestone(sender, instance, created, **kwargs):
    """
    Log important milestones in word learning progress
    """
    try:
        if instance.status in ['learned', 'mastered'] and instance.date_learned:
            # Count total learned words for this user and language
            total_learned = WordsProgress.objects.filter(
                user=instance.user,
                target_language=instance.target_language,
                status__in=['learned', 'mastered']
            ).count()

            # Log milestone achievements
            if total_learned in [1, 5, 10, 25, 50, 100, 250, 500, 1000]:
                logger.info(
                    f"🎉 Milestone achieved! User {instance.user.username} "
                    f"has learned {total_learned} words in {instance.target_language.name_english}"
                )

    except Exception as e:
        logger.error(f"Error in log_word_milestone signal: {str(e)}")