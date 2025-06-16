from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from config.permissions import ReadOnlyForAllSuperadminWritePermission
from .models import Language
from .serializers import LanguageSerializer


class LanguageViewSet(viewsets.ModelViewSet):
    """ViewSet for Language model"""
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = [ReadOnlyForAllSuperadminWritePermission]
    lookup_field = 'code'

    def get_queryset(self):
        """
        Optionally restricts the returned languages to enabled ones,
        by filtering against a `enabled_only` query parameter in the URL.
        """
        queryset = Language.objects.all()
        enabled_only = self.request.query_params.get('enabled_only', None)
        if enabled_only is not None and enabled_only.lower() == 'true':
            queryset = queryset.filter(enabled=True)
        return queryset

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def enabled(self, request):
        """Get list of enabled languages only"""
        enabled_languages = Language.objects.filter(enabled=True)
        serializer = self.get_serializer(enabled_languages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def codes(self, request):
        """Get list of language codes only"""
        enabled_only = request.query_params.get('enabled_only', None)
        queryset = self.get_queryset()
        if enabled_only is not None and enabled_only.lower() == 'true':
            queryset = queryset.filter(enabled=True)
        codes = queryset.values_list('code', flat=True)
        return Response(list(codes))

    @action(detail=True, methods=['get'])
    def by_code(self, request, code=None):
        """Get language by code"""
        try:
            language = self.get_queryset().get(code=code)
            serializer = self.get_serializer(language)
            return Response(serializer.data)
        except Language.DoesNotExist:
            return Response({'error': 'Language not found'}, status=404)
