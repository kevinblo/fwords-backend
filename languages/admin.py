from django.contrib import admin
from .models import Language


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    """Admin configuration for Language model"""
    list_display = ('code', 'name_english', 'name_native', 'enabled', 'created_at', 'updated_at')
    list_filter = ('enabled', 'created_at', 'updated_at')
    search_fields = ('code', 'name_english', 'name_native')
    ordering = ('name_english',)
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('enabled',)

    fieldsets = (
        ('Language Information', {
            'fields': ('code', 'name_english', 'name_native', 'enabled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['enable_languages', 'disable_languages']

    def enable_languages(self, request, queryset):
        """Enable selected languages"""
        updated = queryset.update(enabled=True)
        self.message_user(request, f'{updated} languages were enabled.')

    enable_languages.short_description = "Enable selected languages"

    def disable_languages(self, request, queryset):
        """Disable selected languages"""
        updated = queryset.update(enabled=False)
        self.message_user(request, f'{updated} languages were disabled.')

    disable_languages.short_description = "Disable selected languages"
