from django.urls import path
from . import views

app_name = 'testing'

urlpatterns = [
    # Главная страница (преподаватель/студент)
    path('', views.testing_home, name='home'),
    
    # Работа с группами (преподаватель)
    path('group/create/', views.create_group, name='create_group'),
    path('group/<int:group_id>/', views.group_detail, name='group_detail'),
    path('group/<int:group_id>/delete/', views.delete_group, name='delete_group'),
    
    # Подключение студента
    path('group/join/', views.join_group, name='join_group'),
    
    # Банк вопросов и тесты (преподаватель)
    path('question/create/', views.create_question, name='create_question'),
    path('question/<int:question_id>/', views.question_detail, name='question_detail'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('test/create/', views.create_test, name='create_test'),
    path('test/<int:test_id>/delete/', views.delete_test, name='delete_test'),
    path('test/<int:test_id>/results/', views.test_results, name='test_results'),
    path('attempt/<int:attempt_id>/grade/', views.grade_attempt, name='grade_attempt'),
    
    # Прохождение теста (студент)
    path('test/<int:test_id>/start/', views.start_test, name='start_test'),
    path('attempt/<int:attempt_id>/take/', views.take_test, name='take_test'),
    path('attempt/<int:attempt_id>/result/', views.attempt_result, name='attempt_result'),
]
