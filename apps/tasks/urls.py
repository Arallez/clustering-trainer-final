from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('challenge/<slug:slug>/', views.challenge_detail, name='challenge_detail'),
    path('api/check-solution/', views.check_solution, name='check_solution'),
]
