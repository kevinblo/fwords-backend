from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, LanguageProgress, WordsProgress, QuizProgress
from languages.serializers import LanguageSerializer


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    username = serializers.CharField(write_only=True, required=False, help_text="Full name of the user")

    class Meta:
        model = User
        fields = ('email', 'name', 'username', 'password', 'password_confirm')
        extra_kwargs = {
            'email': {'required': True},
            'name': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # If username is provided, use it as name
        if 'username' in attrs and attrs['username']:
            attrs['name'] = attrs['username']
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        # Remove username from validated_data as it's not a model field
        validated_data.pop('username', None)
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False  # User needs to activate email first
        )
        # Set name if provided
        if 'name' in validated_data:
            user.name = validated_data['name']
            user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password')
            if not user.is_active:
                raise serializers.ValidationError('Account is not activated. Please check your email.')
            if not user.is_email_verified:
                raise serializers.ValidationError('Email is not verified. Please verify your email first.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Email and password are required')

        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile with language preferences"""

    # Read-only nested serializers for displaying language info
    interface_language = LanguageSerializer(read_only=True)
    native_language = LanguageSerializer(read_only=True)
    active_language = LanguageSerializer(read_only=True)

    # Write-only fields for updating language IDs
    interface_language_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    native_language_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    active_language_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    username = serializers.CharField(write_only=True, required=False, help_text="Full name of the user")

    class Meta:
        model = User
        fields = (
            'id', 'email', 'name', 'username', 'is_email_verified', 'created_at', 'updated_at',
            'interface_language', 'native_language', 'active_language', 'notify',
            'interface_language_id', 'native_language_id', 'active_language_id'
        )
        read_only_fields = ('id', 'email', 'is_email_verified', 'created_at', 'updated_at')

    def validate_interface_language_id(self, value):
        """Validate interface language ID"""
        if value is not None:
            from languages.models import Language
            try:
                Language.objects.get(id=value, enabled=True)
                return value
            except Language.DoesNotExist:
                raise serializers.ValidationError('Invalid or disabled language')
        return value

    def validate_native_language_id(self, value):
        """Validate native language ID"""
        if value is not None:
            from languages.models import Language
            try:
                Language.objects.get(id=value, enabled=True)
                return value
            except Language.DoesNotExist:
                raise serializers.ValidationError('Invalid or disabled language')
        return value

    def validate_active_language_id(self, value):
        """Validate active language ID"""
        if value is not None:
            from languages.models import Language
            try:
                Language.objects.get(id=value, enabled=True)
                return value
            except Language.DoesNotExist:
                raise serializers.ValidationError('Invalid or disabled language')
        return value

    def update(self, instance, validated_data):
        """Custom update method with language field mapping and logging"""
        print(f"[SERIALIZER DEBUG] Update called with validated_data: {validated_data}")

        # If username is provided, use it as name
        if 'username' in validated_data and validated_data['username']:
            validated_data['name'] = validated_data.pop('username')

        # Map language ID fields to actual language fields
        language_field_mapping = {
            'interface_language_id': 'interface_language',
            'native_language_id': 'native_language',
            'active_language_id': 'active_language'
        }

        # Process language fields
        for id_field, language_field in language_field_mapping.items():
            if id_field in validated_data:
                language_id = validated_data.pop(id_field)
                if language_id is not None:
                    from languages.models import Language
                    try:
                        language = Language.objects.get(id=language_id, enabled=True)
                        setattr(instance, language_field, language)
                        print(f"[SERIALIZER DEBUG] Setting {language_field} = {language}")
                    except Language.DoesNotExist:
                        print(f"[SERIALIZER ERROR] Language with ID {language_id} not found")
                else:
                    setattr(instance, language_field, None)
                    print(f"[SERIALIZER DEBUG] Setting {language_field} = None")

        # Update other fields
        for field_name, value in validated_data.items():
            print(f"[SERIALIZER DEBUG] Setting {field_name} = {value}")
            setattr(instance, field_name, value)

        # Save the instance
        instance.save()
        print(f"[SERIALIZER DEBUG] Instance saved successfully")

        # Log final state
        print(f"[SERIALIZER DEBUG] Final language states:")
        print(f"  - interface_language: {getattr(instance, 'interface_language', 'NOT_SET')}")
        print(f"  - native_language: {getattr(instance, 'native_language', 'NOT_SET')}")
        print(f"  - active_language: {getattr(instance, 'active_language', 'NOT_SET')}")

        return instance


class EmailActivationSerializer(serializers.Serializer):
    """Serializer for email activation"""
    token = serializers.UUIDField()

    def validate_token(self, value):
        from .models import EmailActivationToken
        try:
            token = EmailActivationToken.objects.get(token=value, is_used=False)
            if token.is_expired():
                raise serializers.ValidationError('Activation token has expired')
            return value
        except EmailActivationToken.DoesNotExist:
            raise serializers.ValidationError('Invalid or expired activation token')


class ResendActivationSerializer(serializers.Serializer):
    """Serializer for resending activation email"""
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if user.is_email_verified:
                raise serializers.ValidationError('Email is already verified')
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist')


class LanguageProgressSerializer(serializers.ModelSerializer):
    """Serializer for language learning progress"""
    language = LanguageSerializer(read_only=True)
    language_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = LanguageProgress
        fields = (
            'id', 'language', 'language_id', 'level',
            'learned_words', 'learned_phrases',
            'updated_at', 'created_at'
        )
        read_only_fields = ('id', 'updated_at', 'created_at')

    def validate_language_id(self, value):
        from languages.models import Language
        try:
            Language.objects.get(id=value, enabled=True)
            return value
        except Language.DoesNotExist:
            raise serializers.ValidationError('Invalid or disabled language')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        language_id = validated_data.pop('language_id')
        
        # Use get_or_create to handle the unique constraint
        from languages.models import Language
        language = Language.objects.get(id=language_id)
        
        progress, created = LanguageProgress.objects.get_or_create(
            user=validated_data['user'],
            language=language,
            defaults=validated_data
        )
        
        # If the record already exists, update it with the new data
        if not created:
            for field, value in validated_data.items():
                setattr(progress, field, value)
            progress.save()
        
        return progress


class WordsProgressSerializer(serializers.ModelSerializer):
    """Serializer for individual word learning progress"""
    # Read-only nested serializers for displaying related info
    word = serializers.SerializerMethodField(read_only=True)
    target_language = LanguageSerializer(read_only=True)
    
    # Write-only fields for creating/updating
    word_id = serializers.IntegerField(write_only=True)
    target_language_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = WordsProgress
        fields = (
            'id', 'word', 'word_id', 'target_language', 'target_language_id',
            'status', 'interval', 'next_review', 'review_count', 'correct_count',
            'date_learned', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_word(self, obj):
        """Get word information"""
        if obj.word:
            return {
                'id': obj.word.id,
                'word': obj.word.word,
                'language': {
                    'id': obj.word.language.id,
                    'code': obj.word.language.code,
                    'name': obj.word.language.name_english
                },
                'transcription': obj.word.transcription,
                'part_of_speech': obj.word.part_of_speech.code if obj.word.part_of_speech else None,
                'difficulty_level': obj.word.difficulty_level
            }
        return None

    def validate_word_id(self, value):
        """Validate word ID"""
        from words.models import Word
        try:
            Word.objects.get(id=value, active=True)
            return value
        except Word.DoesNotExist:
            raise serializers.ValidationError('Invalid or inactive word')

    def validate_target_language_id(self, value):
        """Validate target language ID"""
        from languages.models import Language
        try:
            Language.objects.get(id=value, enabled=True)
            return value
        except Language.DoesNotExist:
            raise serializers.ValidationError('Invalid or disabled language')

    def validate(self, attrs):
        """Validate word language constraints"""
        word_id = attrs.get('word_id')
        target_language_id = attrs.get('target_language_id')
        
        if word_id and target_language_id:
            from words.models import Word
            from languages.models import Language
            
            word = Word.objects.get(id=word_id)
            target_language = Language.objects.get(id=target_language_id)
            
            # Validate that target language must be equal to word language
            if word.language != target_language:
                raise serializers.ValidationError(
                    'Active language must be equal to word language'
                )
            
            # Validate that word language matches user's source language (native_language)
            user = self.context['request'].user
            if user.active_language and word.language == user.native_language:
                raise serializers.ValidationError(
                    'Word and active language mustn\'t match your native language'
                )
        
        return attrs

    def create(self, validated_data):
        """Create new words progress entry"""
        validated_data['user'] = self.context['request'].user
        word_id = validated_data.pop('word_id')
        target_language_id = validated_data.pop('target_language_id')
        
        # Get the related objects
        from words.models import Word
        from languages.models import Language
        word = Word.objects.get(id=word_id)
        target_language = Language.objects.get(id=target_language_id)
        
        # Use get_or_create to handle the unique constraint
        progress, created = WordsProgress.objects.get_or_create(
            user=validated_data['user'],
            word=word,
            target_language=target_language,
            defaults=validated_data
        )
        
        # If the record already exists, update it with the new data
        if not created:
            for field, value in validated_data.items():
                setattr(progress, field, value)
            progress.save()
        
        return progress

    def update(self, instance, validated_data):
        """Update words progress entry"""
        # Handle word_id and target_language_id if provided
        if 'word_id' in validated_data:
            word_id = validated_data.pop('word_id')
            from words.models import Word
            instance.word = Word.objects.get(id=word_id)
        
        if 'target_language_id' in validated_data:
            target_language_id = validated_data.pop('target_language_id')
            from languages.models import Language
            instance.target_language = Language.objects.get(id=target_language_id)
        
        # Update other fields
        for field, value in validated_data.items():
            setattr(instance, field, value)
        
        instance.save()
        return instance


class QuizProgressSerializer(serializers.ModelSerializer):
    """Serializer for quiz progress"""
    language = LanguageSerializer(read_only=True)
    language_id = serializers.IntegerField(write_only=True)
    accuracy_percentage = serializers.ReadOnlyField()

    class Meta:
        model = QuizProgress
        fields = (
            'id', 'language', 'language_id', 'total_questions', 'correct_answers',
            'accuracy_percentage', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_language_id(self, value):
        """Validate language ID"""
        from languages.models import Language
        try:
            Language.objects.get(id=value, enabled=True)
            return value
        except Language.DoesNotExist:
            raise serializers.ValidationError('Invalid or disabled language')

    def validate(self, attrs):
        """Validate quiz data"""
        total_questions = attrs.get('total_questions', 0)
        correct_answers = attrs.get('correct_answers', 0)
        
        if total_questions <= 0:
            raise serializers.ValidationError('Total questions must be greater than 0')
        
        if correct_answers < 0:
            raise serializers.ValidationError('Correct answers cannot be negative')
        
        if correct_answers > total_questions:
            raise serializers.ValidationError('Correct answers cannot exceed total questions')
        
        return attrs

    def create(self, validated_data):
        """Create new quiz progress entry"""
        validated_data['user'] = self.context['request'].user
        language_id = validated_data.pop('language_id')
        
        # Get the language object
        from languages.models import Language
        language = Language.objects.get(id=language_id)
        validated_data['language'] = language
        
        return QuizProgress.objects.create(**validated_data)


class QuizStatsSerializer(serializers.Serializer):
    """Serializer for quiz statistics"""
    language = LanguageSerializer(read_only=True)
    total_questions = serializers.IntegerField(read_only=True)
    average_accuracy = serializers.FloatField(read_only=True)
    quiz_count = serializers.IntegerField(read_only=True)
