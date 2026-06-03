# Migration: задачи используют существующие таблицы simulator_* (перенос из simulator).

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('testing', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='TaskTag',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=100, verbose_name='Название тега')),
                        ('slug', models.SlugField(unique=True, verbose_name='Slug (для URL)')),
                        ('order', models.IntegerField(default=0, verbose_name='Порядок вывода')),
                    ],
                    options={
                        'db_table': 'simulator_tasktag',
                        'ordering': ['order', 'name'],
                        'verbose_name': 'Тег (Блок задач)',
                        'verbose_name_plural': 'Теги задач',
                    },
                ),
                migrations.CreateModel(
                    name='Task',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('title', models.CharField(max_length=200, verbose_name='Название')),
                        ('slug', models.SlugField(help_text="URL-имя, например 'euclidean-dist'", unique=True)),
                        ('description', models.TextField(verbose_name='Описание (HTML)')),
                        ('task_type', models.CharField(choices=[('code', '💻 Написание кода'), ('choice', '📝 Выбор ответа (Тест)')], default='code', max_length=20, verbose_name='Тип задачи')),
                        ('difficulty', models.IntegerField(choices=[(1, '⭐ Novice (Основы)'), (2, '⭐⭐ Beginner (Логика)'), (3, '⭐⭐⭐ Intermediate (Алгоритмы)')], default=1)),
                        ('order', models.IntegerField(default=0, help_text='Позиция внутри тега (должна быть уникальной)', verbose_name='Порядок')),
                        ('function_name', models.CharField(blank=True, help_text='Только для задач с кодом', max_length=100, null=True)),
                        ('initial_code', models.TextField(blank=True, verbose_name='Заготовка кода / Комментарий')),
                        ('solution_code', models.TextField(blank=True, verbose_name='Эталонное решение / Пояснение')),
                        ('test_input', models.JSONField(blank=True, default=dict, verbose_name='Входные данные / Варианты ответа')),
                        ('expected_output', models.JSONField(blank=True, default=dict, verbose_name='Ожидаемый ответ')),
                        ('tags', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tasks', to='tasks.tasktag', verbose_name='Тег (Блок)')),
                    ],
                    options={
                        'db_table': 'simulator_task',
                        'ordering': ['tags__order', 'order'],
                        'constraints': [
                            models.UniqueConstraint(fields=('tags', 'order'), name='unique_task_order_per_tag', violation_error_message='Задание с такой позицией уже существует в этом теге.'),
                        ],
                    },
                ),
                migrations.CreateModel(
                    name='UserTaskAttempt',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('code', models.TextField(verbose_name='Код решения / Ответ пользователя')),
                        ('is_correct', models.BooleanField(default=False, verbose_name='Правильно')),
                        ('error_message', models.TextField(blank=True, null=True, verbose_name='Сообщение об ошибке')),
                        ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата попытки')),
                        ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='tasks.task')),
                        ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='task_attempts', to=settings.AUTH_USER_MODEL)),
                        ('test_attempt', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='task_attempts', to='testing.testattempt', verbose_name='Попытка теста (если в рамках теста)')),
                    ],
                    options={
                        'db_table': 'simulator_usertaskattempt',
                        'ordering': ['-created_at'],
                        'verbose_name': 'Попытка решения',
                        'verbose_name_plural': 'Попытки решений',
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
