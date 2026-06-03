# Ссылка на теги заданий через apps.tasks вместо simulator (только state).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_material_tags_alter_material_order'),
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='material',
                    name='tags',
                    field=models.ManyToManyField(
                        blank=True,
                        help_text='К каким темам задач относится этот материал',
                        related_name='materials',
                        to='tasks.tasktag',
                        verbose_name='Связанные темы',
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
