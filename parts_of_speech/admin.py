from django.contrib import admin
from .models import PartOfSpeech, PartOfSpeechTranslation


class PartOfSpeechTranslationInline(admin.TabularInline):
    """Inline для переводов частей речи"""
    model = PartOfSpeechTranslation
    extra = 1
    fields = ['language', 'name', 'abbreviation']


@admin.register(PartOfSpeech)
class PartOfSpeechAdmin(admin.ModelAdmin):
    """Админ-панель для частей речи"""
    list_display = ['code', 'description', 'enabled', 'created_at']
    list_filter = ['enabled', 'created_at']
    search_fields = ['code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PartOfSpeechTranslationInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('code', 'description', 'enabled')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PartOfSpeechTranslation)
class PartOfSpeechTranslationAdmin(admin.ModelAdmin):
    """Админ-панель для переводов частей речи"""
    list_display = ['part_of_speech', 'language', 'name', 'abbreviation', 'created_at']
    list_filter = ['language', 'part_of_speech', 'created_at']
    search_fields = ['name', 'abbreviation', 'part_of_speech__code']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('part_of_speech', 'language', 'name', 'abbreviation')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
