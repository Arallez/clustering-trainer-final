# Generated manually during testing/tasks integration.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0005_task_related_concepts'),
        ('testing', '0004_remove_question_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='test',
            name='auto_task_score',
            field=models.PositiveIntegerField(default=1, verbose_name='Баллов за автозадание'),
        ),
        migrations.AddField(
            model_name='test',
            name='tasks',
            field=models.ManyToManyField(
                blank=True,
                related_name='testing_tests',
                to='tasks.task',
                verbose_name='Автопроверяемые задания курса',
            ),
        ),
        migrations.AlterField(
            model_name='test',
            name='questions',
            field=models.ManyToManyField(
                blank=True,
                related_name='tests',
                to='testing.question',
                verbose_name='Ручные вопросы из банка',
            ),
        ),
    ]
