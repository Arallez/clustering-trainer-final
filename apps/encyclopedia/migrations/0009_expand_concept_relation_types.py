from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Расширение набора типов связей ConceptRelation.

    Добавляет 8 структурных типов, соответствующих объектным свойствам OWL-онтологии
    (hasParameter, solvesTask, supportsGeometry, assumesClusterSize, hasScalability,
    hasInferenceType, assessesCriterion, helpsSelectParameter), которые ранее
    схлопывались в общий тип RELATED. Новые типы не участвуют в адаптивной
    логике рекомендаций (HARD_RELATION_TYPES и SOFT_RELATION_PRIORITY не
    затрагиваются), но сохраняют полную семантику исходной онтологии в БД.

    После применения миграции необходимо очистить существующие записи
    ConceptRelation и заново выполнить sync_ontology, чтобы связи получили
    корректные типы. Подробности — в docs/relation_types_refactor.md.
    """

    dependencies = [
        ("encyclopedia", "0008_alter_coursemodulesimulator_preset"),
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
                    ("RECOMMENDED_AFTER", "Рекомендуется после"),
                    ("RELATED", "Связано с"),
                    ("EVALUATED_BY", "Оценивается метрикой"),
                    ("EXTENDS", "Расширяет метод"),
                    ("SPECIAL_CASE", "Частный случай"),
                    ("HAS_PARAMETER", "Имеет параметр"),
                    ("SOLVES_TASK", "Решает прикладную задачу"),
                    ("SUPPORTS_GEOMETRY", "Поддерживает геометрию"),
                    ("ASSUMES_CLUSTER_SIZE", "Предполагает размер кластеров"),
                    ("HAS_SCALABILITY", "Имеет масштабируемость"),
                    ("HAS_INFERENCE_TYPE", "Имеет тип логического вывода"),
                    ("ASSESSES_CRITERION", "Оценивает критерий качества"),
                    ("HELPS_SELECT_PARAMETER", "Помогает подобрать параметр"),
                ],
                max_length=30,
                verbose_name="Тип связи",
            ),
        ),
    ]
