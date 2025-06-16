from rest_framework import serializers
from .models import Word, WordTranslation, WordExample, Gender, DifficultyLevel
from languages.serializers import LanguageSerializer
from parts_of_speech.serializers import PartOfSpeechSimpleSerializer


class WordExampleSerializer(serializers.ModelSerializer):
    """Сериализатор для примеров использования слов"""
    translation_language = LanguageSerializer(read_only=True)
    translation_language_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = WordExample
        fields = [
            'id', 'example_text', 'translation', 'translation_language',
            'translation_language_id', 'audio_url', 'active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WordTranslationSerializer(serializers.ModelSerializer):
    """Сериализатор для переводов слов"""
    source_word = serializers.StringRelatedField(read_only=True)
    target_word = serializers.StringRelatedField(read_only=True)
    source_word_id = serializers.IntegerField(write_only=True, required=False)
    target_word_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = WordTranslation
        fields = [
            'id', 'source_word', 'target_word', 'source_word_id', 'target_word_id',
            'confidence', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WordTranslationInlineSerializer(serializers.ModelSerializer):
    """Сериализатор для переводов слов при создании/обновлении слова"""
    target_word_data = serializers.DictField(write_only=True, required=False, help_text="Данные целевого слова для создания")
    target_word_id = serializers.IntegerField(write_only=True, required=False, help_text="ID существующего целевого слова")

    class Meta:
        model = WordTranslation
        fields = ['target_word_data', 'target_word_id', 'confidence', 'notes']

    def validate(self, data):
        """Валидация: должно быть указано либо target_word_data, либо target_word_id"""
        target_word_data = data.get('target_word_data')
        target_word_id = data.get('target_word_id')

        if not target_word_data and not target_word_id:
            raise serializers.ValidationError(
                "Необходимо указать либо target_word_data для создания нового слова, либо target_word_id для связи с существующим"
            )

        if target_word_data and target_word_id:
            raise serializers.ValidationError(
                "Нельзя указывать одновременно target_word_data и target_word_id"
            )

        return data


class WordSerializer(serializers.ModelSerializer):
    """Основной сериализатор для слов"""
    language = LanguageSerializer(read_only=True)
    language_id = serializers.IntegerField(write_only=True)
    part_of_speech = PartOfSpeechSimpleSerializer(read_only=True)
    part_of_speech_id = serializers.IntegerField(write_only=True)
    examples = WordExampleSerializer(many=True, read_only=True)
    translations_as_source = WordTranslationSerializer(many=True, read_only=True)
    translations_as_target = WordTranslationSerializer(many=True, read_only=True)
    all_translations = serializers.SerializerMethodField()
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    difficulty_level_display = serializers.CharField(source='get_difficulty_level_display', read_only=True)

    class Meta:
        model = Word
        fields = [
            'id', 'word', 'language', 'language_id', 'transcription',
            'part_of_speech', 'part_of_speech_id', 'gender', 'gender_display',
            'difficulty_level', 'difficulty_level_display', 'audio_url', 'active',
            'examples', 'translations_as_source', 'translations_as_target',
            'all_translations', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_all_translations(self, obj):
        """Получить все переводы слова в удобном формате"""
        return obj.get_all_translations_dict()


class WordCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления слов с примерами и переводами"""
    examples = WordExampleSerializer(many=True, required=False)
    translations = WordTranslationInlineSerializer(many=True, required=False)

    class Meta:
        model = Word
        fields = [
            'id', 'word', 'language_id', 'transcription', 'part_of_speech_id',
            'gender', 'difficulty_level', 'audio_url', 'active', 'examples',
            'translations', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Создание слова с примерами и переводами"""
        examples_data = validated_data.pop('examples', [])
        translations_data = validated_data.pop('translations', [])

        word = Word.objects.create(**validated_data)

        # Создаем примеры
        for example_data in examples_data:
            WordExample.objects.create(word=word, **example_data)

        # Создаем переводы
        for translation_data in translations_data:
            self._create_translation(word, translation_data)

        return word

    def update(self, instance, validated_data):
        """Обновление слова с примерами и переводами"""
        examples_data = validated_data.pop('examples', [])
        translations_data = validated_data.pop('translations', [])

        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем примеры
        if examples_data:
            # Удаляем существующие примеры
            instance.examples.all().delete()

            # Создаем новые примеры
            for example_data in examples_data:
                WordExample.objects.create(word=instance, **example_data)

        # Обновляем переводы
        if translations_data:
            # Удаляем существующие переводы где это слово является источником
            instance.translations_as_source.all().delete()

            # Создаем новые переводы
            for translation_data in translations_data:
                self._create_translation(instance, translation_data)

        return instance

    def _create_translation(self, source_word, translation_data):
        """Создание перевода для слова с автоматическим созданием обратного перевода"""
        target_word_data = translation_data.get('target_word_data')
        target_word_id = translation_data.get('target_word_id')
        confidence = translation_data.get('confidence', 1.0)
        notes = translation_data.get('notes', '')

        if target_word_data:
            # Создаем новое целевое слово
            target_word = Word.objects.create(**target_word_data)
        else:
            # Используем существующее слово
            try:
                target_word = Word.objects.get(id=target_word_id)
            except Word.DoesNotExist:
                raise serializers.ValidationError(f"Слово с ID {target_word_id} не найдено")

        # Проверяем, что языки разные
        if source_word.language == target_word.language:
            raise serializers.ValidationError("Исходное и целевое слово не могут быть на одном языке")

        # Создаем прямой перевод (если не существует)
        forward_translation, created = WordTranslation.objects.get_or_create(
            source_word=source_word,
            target_word=target_word,
            defaults={
                'confidence': confidence,
                'notes': notes
            }
        )

        # Создаем обратный перевод (если не существует)
        backward_translation, created = WordTranslation.objects.get_or_create(
            source_word=target_word,
            target_word=source_word,
            defaults={
                'confidence': confidence,
                'notes': notes
            }
        )


class WordSimpleSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для слов (для использования в других моделях)"""
    language_code = serializers.CharField(source='language.code', read_only=True)
    part_of_speech_code = serializers.CharField(source='part_of_speech.code', read_only=True)

    class Meta:
        model = Word
        fields = ['id', 'word', 'language_code', 'transcription', 'part_of_speech_code', 'gender']


class WordTranslationCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания переводов слов с автоматическим созданием обратного перевода"""

    class Meta:
        model = WordTranslation
        fields = ['source_word_id', 'target_word_id', 'confidence', 'notes']

    def validate(self, data):
        """Валидация данных перевода"""
        source_word_id = data.get('source_word_id')
        target_word_id = data.get('target_word_id')

        if source_word_id == target_word_id:
            raise serializers.ValidationError("Исходное и целевое слово не могут быть одинаковыми")

        try:
            source_word = Word.objects.get(id=source_word_id)
            target_word = Word.objects.get(id=target_word_id)

            if source_word.language == target_word.language:
                raise serializers.ValidationError("Исходное и целевое слово не могут быть на одном языке")

        except Word.DoesNotExist:
            raise serializers.ValidationError("Одно из слов не существует")

        return data

    def create(self, validated_data):
        """Создание перевода с автоматическим созданием обратного перевода"""
        source_word_id = validated_data['source_word_id']
        target_word_id = validated_data['target_word_id']
        confidence = validated_data.get('confidence', 1.0)
        notes = validated_data.get('notes', '')

        source_word = Word.objects.get(id=source_word_id)
        target_word = Word.objects.get(id=target_word_id)

        # Создаем прямой перевод (если не существует)
        forward_translation, created = WordTranslation.objects.get_or_create(
            source_word=source_word,
            target_word=target_word,
            defaults={
                'confidence': confidence,
                'notes': notes
            }
        )

        # Создаем обратный перевод (если не существует)
        backward_translation, created = WordTranslation.objects.get_or_create(
            source_word=target_word,
            target_word=source_word,
            defaults={
                'confidence': confidence,
                'notes': notes
            }
        )

        return forward_translation


class WordSearchSerializer(serializers.Serializer):
    """Сериализатор для поиска слов"""
    query = serializers.CharField(max_length=200, help_text="Поисковый запрос")
    language = serializers.CharField(max_length=10, required=False, help_text="Код языка для поиска")
    part_of_speech = serializers.CharField(max_length=20, required=False, help_text="Код части речи")
    difficulty_level = serializers.CharField(max_length=30, required=False, help_text="Уровень сложности")
    active_only = serializers.BooleanField(default=True, help_text="Искать только активные слова")


class WordStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики слов"""
    total_words = serializers.IntegerField()
    active_words = serializers.IntegerField()
    words_by_language = serializers.DictField()
    words_by_part_of_speech = serializers.DictField()
    words_by_difficulty_level = serializers.DictField()
    words_with_audio = serializers.IntegerField()
    words_with_examples = serializers.IntegerField()


class WordRandomSerializer(serializers.ModelSerializer):
    """Сериализатор для случайных слов с полной информацией и переводом"""
    language = LanguageSerializer(read_only=True)
    part_of_speech = serializers.SerializerMethodField()
    examples = WordExampleSerializer(many=True, read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    difficulty_level_display = serializers.CharField(source='get_difficulty_level_display', read_only=True)
    translation = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = [
            'id', 'word', 'language', 'transcription', 'part_of_speech',
            'gender', 'gender_display', 'difficulty_level', 'difficulty_level_display',
            'audio_url', 'active', 'examples', 'translation', 'created_at', 'updated_at'
        ]

    def get_part_of_speech(self, obj):
        """Получить часть речи с названием на языке слова"""
        if obj.part_of_speech:
            return {
                'id': obj.part_of_speech.id,
                'code': obj.part_of_speech.code,
                'name': obj.part_of_speech.get_translation(obj.language.code),
                'abbreviation': obj.part_of_speech.get_abbreviation_translation(obj.language.code)
            }
        return None

    def get_translation(self, obj):
        """Получить полную информацию о переводе слова на указанный язык"""
        target_language = self.context.get('target_language')
        if not target_language:
            return None

        # Ищем перевод на указанный язык
        translation = WordTranslation.objects.filter(
            source_word=obj,
            target_word__language__code=target_language
        ).select_related(
            'target_word__language',
            'target_word__part_of_speech'
        ).prefetch_related(
            'target_word__examples'
        ).first()

        if translation:
            target_word = translation.target_word
            return {
                'id': target_word.id,
                'word': target_word.word,
                'language': LanguageSerializer(target_word.language).data,
                'transcription': target_word.transcription,
                'part_of_speech': {
                    'id': target_word.part_of_speech.id,
                    'code': target_word.part_of_speech.code,
                    'name': target_word.part_of_speech.get_translation(target_word.language.code),
                    'abbreviation': target_word.part_of_speech.get_abbreviation_translation(target_word.language.code)
                },
                'gender': target_word.gender,
                'gender_display': target_word.get_gender_display(),
                'difficulty_level': target_word.difficulty_level,
                'difficulty_level_display': target_word.get_difficulty_level_display(),
                'audio_url': target_word.audio_url,
                'active': target_word.active,
                'examples': WordExampleSerializer(target_word.examples.filter(active=True), many=True).data,
                'confidence': translation.confidence,
                'notes': translation.notes,
                'created_at': target_word.created_at,
                'updated_at': target_word.updated_at
            }

        return None
