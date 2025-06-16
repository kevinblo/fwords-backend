from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailActivationToken, LanguageProgress, WordsProgress, QuizProgress


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model"""
    list_display = ('email', 'username', 'is_email_verified', 'is_active', 'created_at')
    list_filter = ('is_email_verified', 'is_active', 'is_staff', 'created_at')
    search_fields = ('email', 'username')
    ordering = ('-created_at',)
    
    # Override fieldsets to remove first_name and last_name
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email',)}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Custom Fields', {
            'fields': ('is_email_verified', 'created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EmailActivationToken)
class EmailActivationTokenAdmin(admin.ModelAdmin):
    """Admin configuration for EmailActivationToken model"""
    list_display = ('user', 'token', 'created_at', 'is_used', 'is_expired_display')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('token', 'created_at')
    ordering = ('-created_at',)
    
    def is_expired_display(self, obj):
        return obj.is_expired()
    is_expired_display.boolean = True
    is_expired_display.short_description = 'Is Expired'


@admin.register(LanguageProgress)
class LanguageProgressAdmin(admin.ModelAdmin):
    """Admin configuration for LanguageProgress model"""
    list_display = ('user', 'language', 'level', 'learned_words', 'learned_phrases', 'updated_at')
    list_filter = ('level', 'language', 'updated_at', 'created_at')
    search_fields = ('user__email', 'user__username', 'language__name_english', 'language__code')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-updated_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'language', 'level')
        }),
        ('Progress', {
            'fields': ('learned_words', 'learned_phrases')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WordsProgress)
class WordsProgressAdmin(admin.ModelAdmin):
    """Admin configuration for WordsProgress model"""
    list_display = (
        'user', 'word_display', 'word_language', 'target_language', 'status', 
        'review_count', 'correct_count', 'accuracy_percentage', 'next_review', 'updated_at'
    )
    list_filter = (
        'status', 'target_language', 'word__language', 'word__difficulty_level',
        'created_at', 'updated_at', 'date_learned'
    )
    search_fields = (
        'user__email', 'user__username', 'word__word', 
        'target_language__name_english', 'target_language__code',
        'word__language__name_english', 'word__language__code'
    )
    readonly_fields = ('created_at', 'updated_at', 'accuracy_percentage')
    ordering = ('-updated_at',)
    
    # Autocomplete fields for better UX
    autocomplete_fields = ['word', 'user']
    # raw_id_fields = ['target_language']
    
    # List per page for better performance
    list_per_page = 50
    list_max_show_all = 200
    
    fieldsets = (
        (None, {
            'fields': ('user', 'word', 'target_language', 'status')
        }),
        ('Spaced Repetition', {
            'fields': ('interval', 'next_review', 'date_learned'),
            'description': 'Spaced repetition system settings'
        }),
        ('Statistics', {
            'fields': ('review_count', 'correct_count', 'accuracy_percentage'),
            'description': 'Learning progress statistics'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Custom display methods
    def word_display(self, obj):
        """Display word with transcription if available"""
        if obj.word.transcription:
            return f"{obj.word.word} [{obj.word.transcription}]"
        return obj.word.word
    word_display.short_description = 'Word'
    word_display.admin_order_field = 'word__word'
    
    def word_language(self, obj):
        """Display word's source language"""
        return f"{obj.word.language.name_english} ({obj.word.language.code})"
    word_language.short_description = 'Word Language'
    word_language.admin_order_field = 'word__language__name_english'
    
    def accuracy_percentage(self, obj):
        """Calculate and display accuracy percentage"""
        if obj.review_count == 0:
            return "No reviews yet"
        accuracy = (obj.correct_count / obj.review_count) * 100
        return f"{accuracy:.1f}%"
    accuracy_percentage.short_description = 'Accuracy'
    
    # Custom actions
    actions = ['mark_as_new', 'mark_as_learning', 'mark_as_learned', 'mark_as_mastered', 'reset_progress']
    
    def mark_as_new(self, request, queryset):
        """Mark selected words as new"""
        updated = queryset.update(status='new')
        self.message_user(request, f'{updated} words marked as new.')
    mark_as_new.short_description = 'Mark selected words as new'
    
    def mark_as_learning(self, request, queryset):
        """Mark selected words as learning"""
        updated = queryset.update(status='learning')
        self.message_user(request, f'{updated} words marked as learning.')
    mark_as_learning.short_description = 'Mark selected words as learning'
    
    def mark_as_learned(self, request, queryset):
        """Mark selected words as learned"""
        from django.utils import timezone
        updated = 0
        for progress in queryset:
            progress.status = 'learned'
            if not progress.date_learned:
                progress.date_learned = timezone.now().date()
            progress.save()
            updated += 1
        self.message_user(request, f'{updated} words marked as learned.')
    mark_as_learned.short_description = 'Mark selected words as learned'
    
    def mark_as_mastered(self, request, queryset):
        """Mark selected words as mastered"""
        from django.utils import timezone
        updated = 0
        for progress in queryset:
            progress.status = 'mastered'
            if not progress.date_learned:
                progress.date_learned = timezone.now().date()
            progress.save()
            updated += 1
        self.message_user(request, f'{updated} words marked as mastered.')
    mark_as_mastered.short_description = 'Mark selected words as mastered'
    
    def reset_progress(self, request, queryset):
        """Reset progress for selected words"""
        updated = queryset.update(
            status='new',
            interval=1,
            next_review=None,
            review_count=0,
            correct_count=0,
            date_learned=None
        )
        self.message_user(request, f'{updated} words progress reset.')
    reset_progress.short_description = 'Reset progress for selected words'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance"""
        return super().get_queryset(request).select_related(
            'user', 'word', 'word__language', 'word__part_of_speech', 'target_language'
        )
    
    # Customize the changelist view
    def changelist_view(self, request, extra_context=None):
        """Add summary statistics to changelist"""
        extra_context = extra_context or {}
        
        # Get summary statistics
        queryset = self.get_queryset(request)
        total_words = queryset.count()
        
        status_counts = {}
        for status, _ in WordsProgress.STATUS_CHOICES:
            status_counts[status] = queryset.filter(status=status).count()
        
        # Calculate overall accuracy
        total_reviews = sum(progress.review_count for progress in queryset)
        total_correct = sum(progress.correct_count for progress in queryset)
        overall_accuracy = (total_correct / total_reviews * 100) if total_reviews > 0 else 0
        
        extra_context['summary_stats'] = {
            'total_words': total_words,
            'status_counts': status_counts,
            'total_reviews': total_reviews,
            'overall_accuracy': f"{overall_accuracy:.1f}%"
        }
        
        return super().changelist_view(request, extra_context)


@admin.register(QuizProgress)
class QuizProgressAdmin(admin.ModelAdmin):
    """Admin configuration for QuizProgress model"""
    list_display = (
        'user', 'language', 'total_questions', 'correct_answers', 
        'accuracy_percentage_display', 'created_at'
    )
    list_filter = ('language', 'created_at', 'updated_at')
    search_fields = (
        'user__email', 'user__name', 
        'language__name_english', 'language__code'
    )
    readonly_fields = ('created_at', 'updated_at', 'accuracy_percentage_display')
    ordering = ('-created_at',)
    
    # Autocomplete fields for better UX
    autocomplete_fields = ['user']
    
    # List per page for better performance
    list_per_page = 50
    list_max_show_all = 200
    
    fieldsets = (
        (None, {
            'fields': ('user', 'language')
        }),
        ('Quiz Results', {
            'fields': ('total_questions', 'correct_answers', 'accuracy_percentage_display'),
            'description': 'Quiz performance data'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Custom display methods
    def accuracy_percentage_display(self, obj):
        """Display accuracy percentage"""
        return f"{obj.accuracy_percentage}%"
    accuracy_percentage_display.short_description = 'Accuracy'
    accuracy_percentage_display.admin_order_field = 'correct_answers'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance"""
        return super().get_queryset(request).select_related('user', 'language')
    
    # Customize the changelist view
    def changelist_view(self, request, extra_context=None):
        """Add summary statistics to changelist"""
        extra_context = extra_context or {}
        
        # Get summary statistics
        queryset = self.get_queryset(request)
        total_quizzes = queryset.count()
        
        if total_quizzes > 0:
            total_questions = sum(quiz.total_questions for quiz in queryset)
            total_correct = sum(quiz.correct_answers for quiz in queryset)
            overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
            
            # Language breakdown
            language_stats = {}
            for quiz in queryset:
                lang_name = quiz.language.name_english
                if lang_name not in language_stats:
                    language_stats[lang_name] = {
                        'count': 0,
                        'total_questions': 0,
                        'total_correct': 0
                    }
                language_stats[lang_name]['count'] += 1
                language_stats[lang_name]['total_questions'] += quiz.total_questions
                language_stats[lang_name]['total_correct'] += quiz.correct_answers
            
            # Calculate accuracy for each language
            for lang_name, stats in language_stats.items():
                if stats['total_questions'] > 0:
                    stats['accuracy'] = (stats['total_correct'] / stats['total_questions']) * 100
                else:
                    stats['accuracy'] = 0
        else:
            total_questions = 0
            total_correct = 0
            overall_accuracy = 0
            language_stats = {}
        
        extra_context['quiz_summary_stats'] = {
            'total_quizzes': total_quizzes,
            'total_questions': total_questions,
            'total_correct': total_correct,
            'overall_accuracy': f"{overall_accuracy:.1f}%",
            'language_stats': language_stats
        }
        
        return super().changelist_view(request, extra_context)