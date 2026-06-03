# Ссылка на задания через apps.tasks вместо simulator.
# Только state: таблица M2M по-прежнему ссылается на simulator_task (теперь это tasks.Task).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testing', '0001_initial'),
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='test',
                    name='tasks',
                    field=models.ManyToManyField(blank=True, related_name='scheduled_tests', to='tasks.task', verbose_name='Задания'),
                ),
            ],
            database_operations=[],
        ),
    ]
