"""
URL configuration for fwords-backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger/OpenAPI schema
schema_view = get_schema_view(
    openapi.Info(
        title="ForeignWords Backend API",
        default_version='v1',
        description="API for language learning application with user authentication, words, and phrases management",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@zanket.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # API v1 endpoints
    path('api/v1/auth/', include('users.urls')),
    path('api/v1/progress/', include('users.urls_progress')),
    path('api/v1/', include('languages.urls')),
    path('api/v1/', include('parts_of_speech.urls')),
    path('api/v1/', include('words.urls')),
    
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
