from rest_framework import serializers
from .models import PartOfSpeech, PartOfSpeechTranslation
from languages.serializers import LanguageSerializer


class PartOfSpeechTranslationSerializer(serializers.ModelSerializer):
    """Сериализатор для переводов частей речи"""
    language = LanguageSerializer(read_only=True)
    language_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = PartOfSpeechTranslation
        fields = [
            'id', 'language', 'language_id', 'name', 'abbreviation',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PartOfSpeechSerializer(serializers.ModelSerializer):
    """Сериализатор для частей речи"""
    translations = PartOfSpeechTranslationSerializer(many=True, read_only=True)
    translations_dict = serializers.SerializerMethodField()
    
    class Meta:
        model = PartOfSpeech
        fields = [
            'id', 'code', 'description', 'enabled', 'translations',
            'translations_dict', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_translations_dict(self, obj):
        """Возвращает переводы в виде словаря {язык: название}"""
        return obj.get_all_translations()


class PartOfSpeechCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления частей речи с переводами"""
    translations = PartOfSpeechTranslationSerializer(many=True, required=False)
    
    class Meta:
        model = PartOfSpeech
        fields = [
            'id', 'code', 'description', 'enabled', 'translations',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Создание части речи с переводами"""
        translations_data = validated_data.pop('translations', [])
        part_of_speech = PartOfSpeech.objects.create(**validated_data)
        
        for translation_data in translations_data:
            PartOfSpeechTranslation.objects.create(
                part_of_speech=part_of_speech,
                **translation_data
            )
        
        return part_of_speech
    
    def update(self, instance, validated_data):
        """Обновление части речи с переводами"""
        translations_data = validated_data.pop('translations', [])
        
        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Обновляем переводы
        if translations_data:
            # Удаляем существующие переводы
            instance.translations.all().delete()
            
            # Создаем новые переводы
            for translation_data in translations_data:
                PartOfSpeechTranslation.objects.create(
                    part_of_speech=instance,
                    **translation_data
                )
        
        return instance


class PartOfSpeechSimpleSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для частей речи (для использования в других моделях)"""
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = PartOfSpeech
        fields = ['id', 'code', 'name']
    
    def get_name(self, obj):
        """Возвращает название части речи на языке запроса"""
        request = self.context.get('request')
        if request and hasattr(request, 'language_code'):
            return obj.get_translation(request.language_code)
        return obj.code