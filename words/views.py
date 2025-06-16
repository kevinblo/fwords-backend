from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count
from config.permissions import ReadOnlyForAllPermission
from .models import Word, WordTranslation, WordExample
from .serializers import (
    WordSerializer,
    WordCreateUpdateSerializer,
    WordTranslationSerializer,
    WordTranslationCreateSerializer,
    WordExampleSerializer,
    WordSimpleSerializer,
    WordSearchSerializer,
    WordStatsSerializer,
    WordRandomSerializer
)


class WordViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления словами.
    
    Поддерживает:
    - CRUD операции для слов
    - Фильтрацию по языку, части речи, роду, активности
    - Поиск по слову и транскрипции
    - Получение переводов для конкретного слова
    - Статистику слов
    """
    queryset = Word.objects.all()
    permission_classes = [ReadOnlyForAllPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['language', 'part_of_speech', 'gender', 'difficulty_level', 'active']
    search_fields = ['word', 'transcription']
    ordering_fields = ['word', 'created_at']
    ordering = ['word']
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action in ['create', 'update', 'partial_update']:
            return WordCreateUpdateSerializer
        elif self.action == 'simple':
            return WordSimpleSerializer
        return WordSerializer
    
    def get_queryset(self):
        """Оптимизированный queryset с prefetch_related"""
        return Word.objects.select_related(
            'language', 'part_of_speech'
        ).prefetch_related(
            'examples__translation_language',
            'translations_as_source__target_word__language',
            'translations_as_target__source_word__language'
        ).all()
    
    @action(detail=False, methods=['get'])
    def simple(self, request):
        """
        Возвращает упрощенный список слов (только основные поля).
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def translations(self, request, pk=None):
        """
        Возвращает все переводы для конкретного слова.
        """
        word = self.get_object()
        translations = word.get_translations()
        serializer = WordTranslationSerializer(translations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_translation(self, request, pk=None):
        """
        Добавляет новый перевод для слова.
        """
        source_word = self.get_object()
        data = request.data.copy()
        data['source_word_id'] = source_word.id
        
        serializer = WordTranslationCreateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def examples(self, request, pk=None):
        """
        Возвращает все примеры использования для конкретного слова.
        """
        word = self.get_object()
        examples = word.examples.filter(active=True)
        serializer = WordExampleSerializer(examples, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_example(self, request, pk=None):
        """
        Добавляет новый пример использования для слова.
        """
        word = self.get_object()
        serializer = WordExampleSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(word=word)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Возвращает только активные слова.
        """
        queryset = self.get_queryset().filter(active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_difficulty(self, request):
        """
        Возвращает слова по уровню сложности.
        Параметр: difficulty_level
        """
        difficulty_level = request.query_params.get('difficulty_level')
        if not difficulty_level:
            return Response(
                {'error': 'Параметр difficulty_level обязателен'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            difficulty_level=difficulty_level,
            active=True
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """
        Расширенный поиск слов с дополнительными параметрами.
        """
        serializer = WordSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        queryset = self.get_queryset()
        
        # Поиск по тексту
        query = data.get('query')
        if query:
            queryset = queryset.filter(
                Q(word__icontains=query) | Q(transcription__icontains=query)
            )
        
        # Фильтр по языку
        language = data.get('language')
        if language:
            queryset = queryset.filter(language__code=language)
        
        # Фильтр по части речи
        part_of_speech = data.get('part_of_speech')
        if part_of_speech:
            queryset = queryset.filter(part_of_speech__code=part_of_speech)
        
        # Фильтр по уровню сложности
        difficulty_level = data.get('difficulty_level')
        if difficulty_level:
            queryset = queryset.filter(difficulty_level=difficulty_level)
        
        # Фильтр по активности
        if data.get('active_only', True):
            queryset = queryset.filter(active=True)
        
        serializer = WordSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Возвращает статистику по словам.
        """
        total_words = Word.objects.count()
        active_words = Word.objects.filter(active=True).count()
        
        # Статистика по языкам
        words_by_language = dict(
            Word.objects.values('language__code', 'language__name_english')
            .annotate(count=Count('id'))
            .values_list('language__code', 'count')
        )
        
        # Статистика по частям речи
        words_by_part_of_speech = dict(
            Word.objects.values('part_of_speech__code')
            .annotate(count=Count('id'))
            .values_list('part_of_speech__code', 'count')
        )
        
        # Статистика по уровням сложности
        words_by_difficulty_level = dict(
            Word.objects.values('difficulty_level')
            .annotate(count=Count('id'))
            .values_list('difficulty_level', 'count')
        )
        
        words_with_audio = Word.objects.exclude(audio_url='').count()
        words_with_examples = Word.objects.filter(examples__isnull=False).distinct().count()
        
        stats_data = {
            'total_words': total_words,
            'active_words': active_words,
            'words_by_language': words_by_language,
            'words_by_part_of_speech': words_by_part_of_speech,
            'words_by_difficulty_level': words_by_difficulty_level,
            'words_with_audio': words_with_audio,
            'words_with_examples': words_with_examples,
        }
        
        serializer = WordStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def random(self, request):
        """
        Возвращает случайные слова с переводами.
        
        Параметры:
        - count: количество слов (по умолчанию 20, максимум 100)
        - from: код исходного языка (обязательный)
        - to: код языка перевода (обязательный)
        - level: уровень сложности слова (необязательный)
        """
        # Получаем параметры
        count = int(request.query_params.get('count', 20))
        source_language = request.query_params.get('from')
        target_language = request.query_params.get('to')
        difficulty_level = request.query_params.get('level')
        
        # Валидация параметров
        if not source_language:
            return Response(
                {'error': 'Параметр "from" (исходный язык) обязателен'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not target_language:
            return Response(
                {'error': 'Параметр "to" (язык перевода) обязателен'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if source_language == target_language:
            return Response(
                {'error': 'Исходный язык и язык перевода не могут быть одинаковыми'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ограничиваем количество слов
        if count > 100:
            count = 100
        elif count < 1:
            count = 1
        
        # Строим базовый queryset
        queryset = Word.objects.filter(
            language__code=source_language,
            active=True
        ).select_related('language', 'part_of_speech')
        
        # Фильтруем по уровню сложности если указан
        if difficulty_level:
            queryset = queryset.filter(difficulty_level=difficulty_level)
        
        # Фильтруем только те слова, у которых есть переводы на целевой язык
        queryset = queryset.filter(
            translations_as_source__target_word__language__code=target_language,
            translations_as_source__target_word__active=True
        ).distinct()
        
        # Проверяем, есть ли слова
        total_words = queryset.count()
        if total_words == 0:
            return Response(
                {
                    'error': f'Не найдено активных слов на языке "{source_language}" с переводами на "{target_language}"'
                    + (f' уровня сложности "{difficulty_level}"' if difficulty_level else '')
                }, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Получаем случайные слова
        # Используем order_by('?') для случайной выборки
        random_words = queryset.order_by('?')[:count]
        
        # Сериализуем с контекстом для получения переводов
        serializer = WordRandomSerializer(
            random_words, 
            many=True, 
            context={'target_language': target_language}
        )
        
        return Response({
            'words': serializer.data,
            'total_available': total_words,
            'requested_count': count,
            'returned_count': len(serializer.data),
            'source_language': source_language,
            'target_language': target_language,
            'difficulty_level': difficulty_level
        })


class WordTranslationViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления переводами слов.
    
    Поддерживает:
    - CRUD операции для переводов
    - Фильтрацию по исходному и целевому языку
    - Поиск по словам и заметкам
    """
    queryset = WordTranslation.objects.all()
    serializer_class = WordTranslationSerializer
    permission_classes = [ReadOnlyForAllPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['source_word__language', 'target_word__language', 'confidence']
    search_fields = ['source_word__word', 'target_word__word', 'notes']
    ordering_fields = ['confidence', 'created_at']
    ordering = ['-confidence', 'source_word__word']
    
    def get_queryset(self):
        """Оптимизированный queryset с select_related"""
        return WordTranslation.objects.select_related(
            'source_word__language', 'target_word__language',
            'source_word__part_of_speech', 'target_word__part_of_speech'
        ).all()
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'create':
            return WordTranslationCreateSerializer
        return WordTranslationSerializer


class WordExampleViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления примерами использования слов.
    
    Поддерживает:
    - CRUD операции для примеров
    - Фильтрацию по слову и языку перевода
    - Поиск по тексту примера и переводу
    """
    queryset = WordExample.objects.all()
    serializer_class = WordExampleSerializer
    permission_classes = [ReadOnlyForAllPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['word', 'translation_language', 'active']
    search_fields = ['example_text', 'translation']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Оптимизированный queryset с select_related"""
        return WordExample.objects.select_related(
            'word__language', 'translation_language'
        ).all()
