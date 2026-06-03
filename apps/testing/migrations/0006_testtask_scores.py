# Generated manually to turn Test.tasks into an ordered/scored through model.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0005_task_related_concepts'),
        ('testing', '0005_test_tasks_auto_task_score'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        'ALTER TABLE testing_test_tasks '
                        'ADD COLUMN IF NOT EXISTS score integer NOT NULL DEFAULT 1;'
                    ),
                    reverse_sql='ALTER TABLE testing_test_tasks DROP COLUMN IF EXISTS score;',
                ),
                migrations.RunSQL(
                    sql=(
                        'ALTER TABLE testing_test_tasks '
                        'ADD COLUMN IF NOT EXISTS "order" integer NOT NULL DEFAULT 0;'
                    ),
                    reverse_sql='ALTER TABLE testing_test_tasks DROP COLUMN IF EXISTS "order";',
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name='TestTask',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('score', models.PositiveIntegerField(default=1, verbose_name='Баллов за задание')),
                        ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                        ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_assignments', to='tasks.task')),
                        ('test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_tasks', to='testing.test')),
                    ],
                    options={
                        'verbose_name': 'Автозадание в контрольной',
                        'verbose_name_plural': 'Автозадания в контрольных',
                        'ordering': ['order', 'task__tags__order', 'task__order', 'task__title'],
                        'db_table': 'testing_test_tasks',
                        'unique_together': {('test', 'task')},
                    },
                ),
                migrations.AlterField(
                    model_name='test',
                    name='tasks',
                    field=models.ManyToManyField(
                        blank=True,
                        related_name='testing_tests',
                        through='testing.TestTask',
                        to='tasks.task',
                        verbose_name='Автопроверяемые задания курса',
                    ),
                ),
            ],
        ),
    ]
