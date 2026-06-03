from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("encyclopedia", "0004_alter_conceptrelation_relation_type_add_recommended_after"),
        ("tasks", "0004_cleanup_curriculum_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="related_concepts",
            field=models.ManyToManyField(
                blank=True,
                help_text="Дополнительные понятия для диагностики ошибок и рекомендаций.",
                related_name="related_tasks",
                to="encyclopedia.concept",
                verbose_name="Побочные понятия",
            ),
        ),
    ]
