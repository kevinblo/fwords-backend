from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from config.permissions import ReadOnlyForAllStaffWritePermission
from .models import PartOfSpeech, PartOfSpeechTranslation
from .serializers import (
    PartOfSpeechSerializer,
    PartOfSpeechCreateUpdateSerializer,
    PartOfSpeechTranslationSerializer,
    PartOfSpeechSimpleSerializer
)


class PartOfSpeechViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления частями речи.
    
    Поддерживает:
    - CRUD операции для частей речи
    - Фильтрацию по enabled статусу
    - Поиск по коду и описанию
    - Получение переводов для конкретной части речи
    """
    queryset = PartOfSpeech.objects.all()
    permission_classes = [ReadOnlyForAllStaffWritePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['enabled']
    search_fields = ['code', 'description']
    ordering_fields = ['code', 'created_at']
    ordering = ['code']
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action in ['create', 'update', 'partial_update']:
            return PartOfSpeechCreateUpdateSerializer
        elif self.action == 'simple':
            return PartOfSpeechSimpleSerializer
        return PartOfSpeechSerializer
    
    def get_queryset(self):
        """Оптимизированный queryset с prefetch_related для переводов"""
        return PartOfSpeech.objects.prefetch_related(
            'translations__language'
        ).all()
    
    @action(detail=False, methods=['get'])
    def simple(self, request):
        """
        Возвращает упрощенный список частей речи (только id, code, name).
        Полезно для dropdown списков и других UI компонентов.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def translations(self, request, pk=None):
        """
        Возвращает все переводы для конкретной части речи.
        """
        part_of_speech = self.get_object()
        translations = part_of_speech.translations.all()
        serializer = PartOfSpeechTranslationSerializer(translations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_translation(self, request, pk=None):
        """
        Добавляет новый перевод для части речи.
        """
        part_of_speech = self.get_object()
        serializer = PartOfSpeechTranslationSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(part_of_speech=part_of_speech)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def enabled(self, request):
        """
        Возвращает только активные части речи.
        """
        queryset = self.get_queryset().filter(enabled=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PartOfSpeechTranslationViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления переводами частей речи.
    
    Поддерживает:
    - CRUD операции для переводов
    - Фильтрацию по языку и части речи
    - Поиск по названию и сокращению
    """
    queryset = PartOfSpeechTranslation.objects.all()
    serializer_class = PartOfSpeechTranslationSerializer
    permission_classes = [ReadOnlyForAllStaffWritePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['language', 'part_of_speech']
    search_fields = ['name', 'abbreviation']
    ordering_fields = ['name', 'created_at']
    ordering = ['part_of_speech__code', 'language__code']
    
    def get_queryset(self):
        """Оптимизированный queryset с select_related"""
        return PartOfSpeechTranslation.objects.select_related(
            'part_of_speech', 'language'
        ).all()
