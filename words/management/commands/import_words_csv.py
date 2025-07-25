from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from words.csv_import import WordCSVImporter, CSVImportError
import os


class Command(BaseCommand):
    help = 'Импорт слов из CSV файла'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Путь к CSV файлу')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        
        if not os.path.exists(csv_file_path):
            self.stdout.write(
                self.style.ERROR(f'Файл {csv_file_path} не найден')
            )
            return
        
        try:
            with open(csv_file_path, 'rb') as f:
                csv_file = ContentFile(f.read(), name=os.path.basename(csv_file_path))
                
                importer = WordCSVImporter()
                result = importer.import_from_file(csv_file)
                
                # Выводим результаты
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Импорт завершен!\n'
                        f'Создано слов: {result["created_words"]}\n'
                        f'Создано переводов: {result["created_translations"]}\n'
                        f'Пропущено строк: {result["skipped_rows"]}'
                    )
                )
                
                # Выводим предупреждения
                if result['warnings']:
                    self.stdout.write(self.style.WARNING('\nПредупреждения:'))
                    for warning in result['warnings']:
                        self.stdout.write(self.style.WARNING(f'  - {warning}'))
                
                # Выводим ошибки
                if result['errors']:
                    self.stdout.write(self.style.ERROR('\nОшибки:'))
                    for error in result['errors']:
                        self.stdout.write(self.style.ERROR(f'  - {error}'))
                        
        except CSVImportError as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка импорта: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Неожиданная ошибка: {str(e)}')
            )
