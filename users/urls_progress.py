from django.urls import path
from . import views

# Progress URLs
urlpatterns = [
    path('language/', views.LanguageProgressListCreateView.as_view(), name='language-progress-list'),
    path('language/<int:pk>/', views.LanguageProgressDetailView.as_view(), name='language-progress-detail'),
    path('words/', views.WordsProgressListCreateView.as_view(), name='words-progress-list'),
    path('words/<int:pk>/', views.WordsProgressDetailView.as_view(), name='words-progress-detail'),
    # path('words/bulk-update/', views.WordsProgressBulkUpdateView.as_view(), name='words-progress-bulk-update'),

    path('words-learned-today/', views.WordsLearnedTodayView.as_view(), name='words-learned-today'),
    path('words-stats/', views.WordsLearnedStatsView.as_view(), name='words-learned-stats'),
    
    # Quiz progress URLs
    path('quiz/', views.QuizProgressListCreateView.as_view(), name='quiz-progress-list'),
    path('quiz/<int:pk>/', views.QuizProgressDetailView.as_view(), name='quiz-progress-detail'),
    path('quiz-stats/', views.QuizStatsView.as_view(), name='quiz-stats'),
]