from django.urls import path, reverse_lazy
from django.views.generic import RedirectView
from . import views

app_name = 'simulator'

urlpatterns = [
    # Песочница: одна страница + API для запуска алгоритмов
    path('', views.index, name='index'),
    path('run/', views.run_algorithm, name='run_algorithm'),

    # Редиректы со старых URL заданий на /tasks/
    path('tasks/', RedirectView.as_view(url=reverse_lazy('tasks:task_list'), permanent=False)),
    path('challenge/<slug:slug>/', views._redirect_legacy_challenge),
    
    # Utilities
    path('dendrogram/', views.get_dendrogram, name='get_dendrogram'),
    path('preset/', views.get_preset, name='get_preset'),
]
