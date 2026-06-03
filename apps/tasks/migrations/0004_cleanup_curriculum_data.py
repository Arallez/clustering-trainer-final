from django.db import migrations


MODULE_TAGS = {
    "module-1": ("Модуль 1. Что такое кластеризация", 10),
    "module-2": ("Модуль 2. Метрические алгоритмы разбиения", 20),
    "module-3": ("Модуль 3. Плотностные алгоритмы", 30),
    "module-4": ("Модуль 4. Иерархические методы", 40),
    "module-5": ("Модуль 5. Модельные и графовые методы", 50),
    "module-6": ("Модуль 6. Принятие решений в кластер-анализе", 60),
}


def cleanup_curriculum_data(apps, schema_editor):
    TaskTag = apps.get_model("tasks", "TaskTag")
    Task = apps.get_model("tasks", "Task")
    Material = apps.get_model("materials", "Material")
    Concept = apps.get_model("encyclopedia", "Concept")

    def get_concept(uri):
        if not uri:
            return None
        return Concept.objects.filter(uri=uri).only("id").first()

    tags = {}
    for slug, (name, order) in MODULE_TAGS.items():
        tag, _ = TaskTag.objects.get_or_create(slug=slug, defaults={"name": name, "order": order})
        tag.name = name
        tag.order = order
        tag.save(update_fields=["name", "order"])
        tags[slug] = tag

    task_updates = {
        "euclidean-distance": {"tag": "module-1", "order": 10, "concept": None},
        "find-centroid": {"tag": "module-1", "order": 20, "concept": None},
        "algoritmy-razbieniya": {"tag": "module-1", "order": 30, "concept": "PartitioningAlgorithm"},
        "test-quiz-euclidean": {"tag": "module-1", "order": 40, "concept": "Metric_PointDistance"},
        "test-quiz-nonflat": {"tag": "module-1", "order": 50, "concept": "NonFlatGeometry"},
        "kmeans-quiz-basic": {"tag": "module-2", "order": 10, "concept": "Algo_KMeans"},
        "assign-cluster": {"tag": "module-2", "order": 20, "concept": "Algo_KMeans"},
        "centroid-calc": {"tag": "module-2", "order": 30, "concept": "Algo_KMeans"},
        "assign-clusters": {"tag": "module-2", "order": 40, "concept": "Algo_KMeans"},
        "kmeans-final-quiz": {"tag": "module-2", "order": 50, "concept": "Algo_KMeans"},
        "test-code-kmeans": {"tag": "module-2", "order": 60, "concept": "Algo_KMeans"},
        "test-code-minibatch": {"tag": "module-2", "order": 70, "concept": "Algo_MiniBatchKMeans"},
        "test-code-dbscan": {"tag": "module-3", "order": 10, "concept": "Algo_DBSCAN"},
        "test-code-hdbscan": {"tag": "module-3", "order": 20, "concept": "Algo_HDBSCAN"},
    }

    for slug, config in task_updates.items():
        task = Task.objects.filter(slug=slug).first()
        if not task:
            continue
        task.tags = tags[config["tag"]]
        task.order = config["order"]
        task.concept = get_concept(config["concept"])
        task.save(update_fields=["tags", "order", "concept"])

    Task.objects.filter(slug__in=["euclidean-dist", "121", "aa", "122222", "maxmin"]).delete()

    concept = get_concept("Algo_KMeans")
    material_table = schema_editor.quote_name(Material._meta.db_table)
    order_column = schema_editor.quote_name("order")
    concept_column = schema_editor.quote_name("concept_id")
    slug_column = schema_editor.quote_name("slug")

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE {material_table}
            SET {order_column} = %s, {concept_column} = %s
            WHERE {slug_column} = %s
            """,
            [110, concept.id if concept else None, "k-means-theory"],
        )
        cursor.execute(
            f"DELETE FROM {material_table} WHERE {slug_column} = %s",
            ["theory-kmeans"],
        )

    old_tag_slugs = ["basics", "general", "kmeans", "kmeans-code", "kmeans-theory", "11111"]
    tag_table = schema_editor.quote_name(TaskTag._meta.db_table)
    placeholders = ", ".join(["%s"] * len(old_tag_slugs))
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f"DELETE FROM {tag_table} WHERE {slug_column} IN ({placeholders})",
            old_tag_slugs,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("materials", "0001_initial"),
        ("tasks", "0003_fix_algorithm_task_concepts"),
    ]

    operations = [
        migrations.RunPython(cleanup_curriculum_data, migrations.RunPython.noop),
    ]
