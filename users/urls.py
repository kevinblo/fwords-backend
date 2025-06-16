from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# Auth URLs
urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('login/', views.UserLoginView.as_view(), name='user-login'),
    path('logout/', views.logout_view, name='user-logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('activate/<uuid:token>/', views.activate_email, name='activate-email'),
    path('resend-activation/', views.ResendActivationView.as_view(), name='resend-activation'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
]