from django.contrib import admin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path

from .csv_import import WordCSVImporter, CSVImportError
from .forms import CSVImportForm
from .models import Word, WordTranslation, WordExample


class WordTranslationInline(admin.TabularInline):
    """Inline для переводов слов"""
    model = WordTranslation
    fk_name = 'source_word'
    extra = 1
    fields = ['target_word', 'confidence', 'notes']
    autocomplete_fields = ['target_word']
    verbose_name = "Перевод"
    verbose_name_plural = "Переводы"


class WordExampleInline(admin.TabularInline):
    """Inline для примеров использования слов"""
    model = WordExample
    extra = 1
    fields = ['example_text', 'translation', 'translation_language', 'audio_url', 'active']
    verbose_name = "Пример"
    verbose_name_plural = "Примеры"


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    """Админ-панель для слов"""
    list_display = ['word', 'language', 'part_of_speech', 'gender', 'difficulty_level', 'transcription', 'active', 'created_at']
    list_filter = ['language', 'part_of_speech', 'gender', 'difficulty_level', 'active', 'created_at']
    search_fields = ['word', 'transcription', 'language__name_english', 'language__code']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [WordTranslationInline, WordExampleInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('word', 'language', 'transcription', 'part_of_speech')
        }),
        ('Дополнительные свойства', {
            'fields': ('gender', 'difficulty_level', 'audio_url', 'active')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        """Добавляем URL для импорта CSV"""
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='words_word_import_csv'),
        ]
        return custom_urls + urls

    def import_csv(self, request):
        """Представление для импорта CSV"""
        if request.method == 'POST':
            form = CSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    csv_file = form.cleaned_data['csv_file']
                    importer = WordCSVImporter()
                    result = importer.import_from_file(csv_file)

                    # Формируем сообщение о результатах импорта
                    success_msg = f"Импорт завершен! Создано слов: {result['created_words']}, переводов: {result['created_translations']}"
                    if result['skipped_rows'] > 0:
                        success_msg += f", пропущено строк: {result['skipped_rows']}"

                    messages.success(request, success_msg)

                    # Добавляем предупреждения
                    for warning in result['warnings']:
                        messages.warning(request, warning)

                    # Добавляем ошибки
                    for error in result['errors']:
                        messages.error(request, error)

                    return redirect('..')

                except CSVImportError as e:
                    messages.error(request, f"Ошибка импорта: {str(e)}")
                except Exception as e:
                    messages.error(request, f"Неожиданная ошибка: {str(e)}")
        else:
            form = CSVImportForm()

        context = {
            'form': form,
            'title': 'Импорт слов из CSV',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }

        return render(request, 'admin/words/word/import_csv.html', context)

    def changelist_view(self, request, extra_context=None):
        """Добавляем кнопку импорта в список"""
        extra_context = extra_context or {}
        extra_context['import_csv_url'] = 'import-csv/'
        return super().changelist_view(request, extra_context)

    def get_queryset(self, request):
        """Оптимизированный queryset"""
        return super().get_queryset(request).select_related(
            'language', 'part_of_speech'
        )


@admin.register(WordTranslation)
class WordTranslationAdmin(admin.ModelAdmin):
    """Админ-панель для переводов слов"""
    list_display = ['source_word', 'source_language', 'target_word', 'target_language', 'confidence', 'created_at']
    list_filter = ['source_word__language', 'target_word__language', 'confidence', 'created_at']
    search_fields = ['source_word__word', 'target_word__word', 'notes']
    autocomplete_fields = ['source_word', 'target_word']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Перевод', {
            'fields': ('source_word', 'target_word', 'confidence')
        }),
        ('Дополнительная информация', {
            'fields': ('notes',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def source_language(self, obj):
        """Язык исходного слова"""
        return obj.source_word.language.name_english
    source_language.short_description = 'Исходный язык'

    def target_language(self, obj):
        """Язык целевого слова"""
        return obj.target_word.language.name_english
    target_language.short_description = 'Целевой язык'

    def get_queryset(self, request):
        """Оптимизированный queryset"""
        return super().get_queryset(request).select_related(
            'source_word__language', 'target_word__language'
        )


@admin.register(WordExample)
class WordExampleAdmin(admin.ModelAdmin):
    """Админ-панель для примеров использования слов"""
    list_display = ['word', 'word_language', 'example_text_short', 'translation_language', 'active', 'created_at']
    list_filter = ['word__language', 'translation_language', 'active', 'created_at']
    search_fields = ['word__word', 'example_text', 'translation']
    autocomplete_fields = ['word']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Основная информация', {
            'fields': ('word', 'example_text', 'translation', 'translation_language')
        }),
        ('Дополнительные свойства', {
            'fields': ('audio_url', 'active')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def word_language(self, obj):
        """Язык слова"""
        return obj.word.language.name_english
    word_language.short_description = 'Язык слова'

    def example_text_short(self, obj):
        """Сокращенный текст примера"""
        return obj.example_text[:50] + '...' if len(obj.example_text) > 50 else obj.example_text
    example_text_short.short_description = 'Пример'

    def get_queryset(self, request):
        """Оптимизированный queryset"""
        return super().get_queryset(request).select_related(
            'word__language', 'translation_language'
        )