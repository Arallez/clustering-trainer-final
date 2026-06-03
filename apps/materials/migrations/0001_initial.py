from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0006_materialprogress'),
        ('encyclopedia', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='Material',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('title', models.CharField(max_length=200, verbose_name='Заголовок')),
                        ('slug', models.SlugField(unique=True, verbose_name='URL Slug')),
                        ('content', models.TextField(verbose_name='Содержание (HTML)')),
                        ('order', models.IntegerField(default=0, verbose_name='Порядок (сортировка)')),
                        ('created_at', models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name='Дата создания')),
                        ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлено')),
                        ('concept', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='materials', to='encyclopedia.concept', verbose_name='Связанный концепт')),
                    ],
                    options={
                        'verbose_name': 'Материал',
                        'verbose_name_plural': 'Материалы',
                        'ordering': ['order', 'title'],
                        'db_table': 'core_material',
                    },
                ),
                migrations.CreateModel(
                    name='MaterialProgress',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('first_opened_at', models.DateTimeField(blank=True, null=True, verbose_name='Первое открытие')),
                        ('last_opened_at', models.DateTimeField(blank=True, null=True, verbose_name='Последнее открытие')),
                        ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Отмечен как изученный')),
                        ('open_count', models.PositiveIntegerField(default=0, verbose_name='Количество открытий')),
                        ('material', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress_entries', to='materials.material')),
                        ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='material_progress', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'verbose_name': 'Прогресс по материалу',
                        'verbose_name_plural': 'Прогресс по материалам',
                        'ordering': ['-last_opened_at', '-completed_at'],
                        'db_table': 'core_materialprogress',
                    },
                ),
                migrations.AddConstraint(
                    model_name='materialprogress',
                    constraint=models.UniqueConstraint(fields=('user', 'material'), name='unique_user_material_progress'),
                ),
            ],
        ),
    ]
