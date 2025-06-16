import csv
import io
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Word, WordTranslation, DifficultyLevel
from languages.models import Language
from parts_of_speech.models import PartOfSpeech


class CSVImportError(Exception):
    """Исключение для ошибок импорта CSV"""
    pass


class WordCSVImporter:
    """Класс для импорта слов из CSV файла"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.created_words = 0
        self.created_translations = 0
        self.skipped_rows = 0
    
    def import_from_file(self, csv_file):
        """Импорт слов из CSV файла"""
        try:
            content = csv_file.read().decode('utf-8')
            csv_file.seek(0)
            return self.import_from_content(content)
        except UnicodeDecodeError:
            raise CSVImportError("Ошибка кодировки файла. Используйте UTF-8.")
    
    def import_from_content(self, content):
        """Импорт слов из содержимого CSV"""
        reader = csv.DictReader(io.StringIO(content))
        
        required_columns = [
            'source_language_code', 'target_language_code', 
            'word', 'translation', 'transcription', 
            'audio_url', 'level'
        ]
        
        part_of_speech_col = None
        if 'part_of_speech' in reader.fieldnames:
            part_of_speech_col = 'part_of_speech'
        elif 'part_f_speech' in reader.fieldnames:
            part_of_speech_col = 'part_f_speech'
        else:
            required_columns.append('part_of_speech')
        
        if not all(col in reader.fieldnames for col in required_columns):
            missing_cols = [col for col in required_columns if col not in reader.fieldnames]
            raise CSVImportError(f"Отсутствуют обязательные колонки: {', '.join(missing_cols)}")
        
        with transaction.atomic():
            for row_num, row in enumerate(reader, start=2):
                try:
                    self._process_row(row, row_num, part_of_speech_col)
                except Exception as e:
                    self.errors.append(f"Строка {row_num}: {str(e)}")
                    self.skipped_rows += 1
        
        return {
            'created_words': self.created_words,
            'created_translations': self.created_translations,
            'skipped_rows': self.skipped_rows,
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def _process_row(self, row, row_num, part_of_speech_col):
        """Обработка одной строки CSV"""
        source_lang_code = row['source_language_code'].strip().lower()
        target_lang_code = row['target_language_code'].strip().lower()
        word_text = row['word'].strip()
        translation_text = row['translation'].strip()
        transcription = row['transcription'].strip()
        audio_url = row['audio_url'].strip()
        part_of_speech_code = row[part_of_speech_col].strip() if part_of_speech_col else ''
        level = row['level'].strip().upper()
        
        if not all([source_lang_code, target_lang_code, word_text, translation_text, part_of_speech_code]):
            raise ValidationError("Обязательные поля не могут быть пустыми")
        
        try:
            source_language = Language.objects.get(code=source_lang_code)
        except Language.DoesNotExist:
            raise ValidationError(f"Язык с кодом '{source_lang_code}' не найден")
        
        try:
            target_language = Language.objects.get(code=target_lang_code)
        except Language.DoesNotExist:
            raise ValidationError(f"Язык с кодом '{target_lang_code}' не найден")
        
        try:
            part_of_speech = PartOfSpeech.objects.get(code=part_of_speech_code)
        except PartOfSpeech.DoesNotExist:
            raise ValidationError(f"Часть речи с кодом '{part_of_speech_code}' не найдена")
        
        if level:
            level_choices = dict(DifficultyLevel.choices)
            if level not in level_choices:
                level_mapping = {v.lower(): k for k, v in level_choices.items()}
                level_lower = level.lower()
                if level_lower in level_mapping:
                    level = level_mapping[level_lower]
                else:
                    for choice_key, choice_value in level_choices.items():
                        if level_lower in choice_value.lower() or choice_value.lower() in level_lower:
                            level = choice_key
                            break
                    else:
                        self.warnings.append(f"Строка {row_num}: Неизвестный уровень '{level}', используется 'beginner'")
                        level = DifficultyLevel.BEGINNER
        else:
            level = DifficultyLevel.BEGINNER
        
        source_word, created = Word.objects.get_or_create(
            word=word_text,
            language=source_language,
            defaults={
                'transcription': transcription,
                'part_of_speech': part_of_speech,
                'difficulty_level': level,
                'audio_url': audio_url,
            }
        )
        
        if created:
            self.created_words += 1
        else:
            updated = False
            if not source_word.transcription and transcription:
                source_word.transcription = transcription
                updated = True
            if not source_word.audio_url and audio_url:
                source_word.audio_url = audio_url
                updated = True
            if updated:
                source_word.save()
        
        target_word, created = Word.objects.get_or_create(
            word=translation_text,
            language=target_language,
            defaults={
                'part_of_speech': part_of_speech,
                'difficulty_level': level,
            }
        )
        
        if created:
            self.created_words += 1
        
        translation, created = WordTranslation.objects.get_or_create(
            source_word=source_word,
            target_word=target_word,
            defaults={
                'confidence': 1.0,
                'notes': f'Импортировано из CSV (часть речи: {part_of_speech.code})'
            }
        )
        
        if created:
            self.created_translations += 1
        else:
            if 'Импортировано из CSV' not in translation.notes:
                translation.notes += f' | Импортировано из CSV (часть речи: {part_of_speech.code})'
                translation.save()
