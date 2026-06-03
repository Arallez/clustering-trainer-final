# Migration created on 2026-04-12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("encyclopedia", "0002_alter_conceptrelation_relation_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="conceptrelation",
            name="relation_type",
            field=models.CharField(
                choices=[
                    ("IS_A", "Является (Is A)"),
                    ("PART_OF", "Является частью"),
                    ("USES", "Использует"),
                    ("DEPENDS", "Зависит от (Пререквизит)"),
                    ("RELATED", "Связано с"),
                    ("EVALUATED_BY", "Оценивается метрикой"),
                    ("EXTENDS", "Расширяет метод"),
                    ("SPECIAL_CASE", "Частный случай"),
                ],
                max_length=20,
                verbose_name="Тип связи",
            ),
        ),
    ]
