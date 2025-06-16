from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PartOfSpeechViewSet, PartOfSpeechTranslationViewSet

# Создаем роутер для автоматической генерации URL
router = DefaultRouter()
router.register(r'pos', PartOfSpeechViewSet, basename='partsofspeech')
router.register(r'pos/tr', PartOfSpeechTranslationViewSet, basename='partsofspeechtranslation')

urlpatterns = [
    path('', include(router.urls)),
]