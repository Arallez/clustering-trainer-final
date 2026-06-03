from django.urls import path
from . import views

# Import recommendation view — function is called recommendations_view
from apps.encyclopedia.views import recommendations_view

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    
    # Learning Path (Recommendations) — standalone, not inside encyclopedia
    path('learning-path/', recommendations_view, name='learning_path'),
    
    # Secure auth views
    path('login/', views.AccountLoginView.as_view(), name='login'),
    path('logout/', views.AccountLogoutView.as_view(), name='logout'),
]
