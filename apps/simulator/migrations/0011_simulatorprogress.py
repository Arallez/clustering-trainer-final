# Migration created on 2026-04-28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('simulator', '0010_remove_task_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='SimulatorProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('module_slug', models.SlugField(verbose_name='Модуль курса')),
                ('algorithm', models.CharField(max_length=64, verbose_name='Алгоритм')),
                ('preset', models.CharField(blank=True, max_length=64, verbose_name='Датасет')),
                ('run_count', models.PositiveIntegerField(default=0, verbose_name='Количество запусков')),
                ('first_run_at', models.DateTimeField(blank=True, null=True, verbose_name='Первый запуск')),
                ('last_run_at', models.DateTimeField(blank=True, null=True, verbose_name='Последний запуск')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Засчитано')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='simulator_progress', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Прогресс по симулятору',
                'verbose_name_plural': 'Прогресс по симулятору',
                'ordering': ['-last_run_at', '-completed_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='simulatorprogress',
            constraint=models.UniqueConstraint(fields=('user', 'module_slug', 'algorithm', 'preset'), name='unique_user_simulator_progress'),
        ),
    ]
