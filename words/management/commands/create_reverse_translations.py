from django.core.management.base import BaseCommand
from words.models import WordTranslation


class Command(BaseCommand):
    help = 'Создает обратные переводы для всех существующих переводов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет сделано, но не выполнять изменения',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('РЕЖИМ ПРЕДВАРИТЕЛЬНОГО ПРОСМОТРА - изменения не будут сохранены')
            )
        
        # Получаем все существующие переводы
        existing_translations = WordTranslation.objects.all()
        created_count = 0
        skipped_count = 0
        
        self.stdout.write(f'Найдено {existing_translations.count()} существующих переводов')
        
        for translation in existing_translations:
            source = translation.source_word
            target = translation.target_word
            
            # Проверяем, есть ли уже обратный перевод
            reverse_exists = WordTranslation.objects.filter(
                source_word=target,
                target_word=source
            ).exists()
            
            if not reverse_exists:
                if not dry_run:
                    # Создаем обратный перевод
                    WordTranslation.objects.create(
                        source_word=target,
                        target_word=source,
                        confidence=translation.confidence,
                        notes=translation.notes
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{"[БУДЕТ СОЗДАН]" if dry_run else "Создан"} обратный перевод: '
                        f'{target.word} ({target.language.code}) -> {source.word} ({source.language.code})'
                    )
                )
                created_count += 1
            else:
                self.stdout.write(
                    f'Обратный перевод уже существует: '
                    f'{target.word} ({target.language.code}) -> {source.word} ({source.language.code})'
                )
                skipped_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nПредварительный просмотр завершен:\n'
                    f'- Будет создано: {created_count} обратных переводов\n'
                    f'- Пропущено (уже существуют): {skipped_count} переводов\n'
                    f'Запустите команду без --dry-run для применения изменений'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nОбработка завершена:\n'
                    f'- Создано: {created_count} обратных переводов\n'
                    f'- Пропущено (уже существуют): {skipped_count} переводов'
                )
            )