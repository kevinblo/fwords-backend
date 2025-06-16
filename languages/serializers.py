from rest_framework import serializers
from .models import Language


class LanguageSerializer(serializers.ModelSerializer):
    """Serializer for Language model"""

    class Meta:
        model = Language
        fields = ['id', 'code', 'name_english', 'name_native', 'enabled', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
