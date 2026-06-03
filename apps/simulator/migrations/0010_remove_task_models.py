# Удаляем модели заданий из state симулятора (таблицы остаются, ими владеет apps.tasks).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('simulator', '0009_usertaskattempt_test_attempt'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name='UserTaskAttempt'),
                migrations.DeleteModel(name='Task'),
                migrations.DeleteModel(name='TaskTag'),
            ],
            database_operations=[],
        ),
    ]
