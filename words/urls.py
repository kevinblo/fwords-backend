from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WordViewSet, WordTranslationViewSet, WordExampleViewSet

# Создаем роутер для автоматической генерации URL
router = DefaultRouter()
router.register(r'words', WordViewSet, basename='word')
router.register(r'words/tr', WordTranslationViewSet, basename='wordtranslation')
router.register(r'words/examples', WordExampleViewSet, basename='wordexample')

urlpatterns = [
    path('', include(router.urls)),
]