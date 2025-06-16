from django.core.management.base import BaseCommand
from languages.models import Language


class Command(BaseCommand):
    help = 'Load initial languages into the database'

    def handle(self, *args, **options):
        languages_data = [
            {'code': 'en', 'name_english': 'English', 'name_native': 'English', 'enabled': True},
            {'code': 'ru', 'name_english': 'Russian', 'name_native': 'Русский', 'enabled': True},
            {'code': 'es', 'name_english': 'Spanish', 'name_native': 'Español', 'enabled': True},
            {'code': 'fr', 'name_english': 'French', 'name_native': 'Français', 'enabled': False},
            {'code': 'de', 'name_english': 'German', 'name_native': 'Deutsch', 'enabled': False},
            {'code': 'it', 'name_english': 'Italian', 'name_native': 'Italiano', 'enabled': False},
            {'code': 'pt', 'name_english': 'Portuguese', 'name_native': 'Português', 'enabled': False},
            {'code': 'zh', 'name_english': 'Chinese', 'name_native': '中文', 'enabled': False},
            {'code': 'ja', 'name_english': 'Japanese', 'name_native': '日本語', 'enabled': False},
            {'code': 'ko', 'name_english': 'Korean', 'name_native': '한국어', 'enabled': False},
        ]

        created_count = 0
        updated_count = 0

        for lang_data in languages_data:
            language, created = Language.objects.get_or_create(
                code=lang_data['code'],
                defaults={
                    'name_english': lang_data['name_english'],
                    'name_native': lang_data['name_native'],
                    'enabled': lang_data['enabled']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created language: {language}')
                )
            else:
                # Update existing language if data differs
                if (language.name_english != lang_data['name_english'] or 
                    language.name_native != lang_data['name_native'] or
                    language.enabled != lang_data['enabled']):
                    language.name_english = lang_data['name_english']
                    language.name_native = lang_data['name_native']
                    language.enabled = lang_data['enabled']
                    language.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated language: {language}')
                    )
                else:
                    self.stdout.write(f'Language already exists: {language}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {created_count} languages created, {updated_count} languages updated'
            )
        )