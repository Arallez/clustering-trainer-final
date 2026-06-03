from django.urls import path
from . import views

app_name = 'encyclopedia'

urlpatterns = [
    path('', views.graph_view, name='graph'),
    path('list/', views.concept_list, name='list'),
    path('concept/<int:pk>/', views.concept_detail, name='detail'),
    path('concept/<int:pk>/articles/', views.concept_articles_api, name='concept_articles_api'),
    path('recommendations/', views.recommendations_view, name='recommendations'),
]
