from django.db import migrations, models
import django.db.models.deletion


MODULES = [
    {
        "slug": "module-1",
        "order": 1,
        "title": "Модуль 1. Что такое кластеризация",
        "subtitle": "База",
        "summary": "Базовые понятия, похожесть объектов, расстояния и геометрия данных.",
        "highlights": [
            "кластеризация как обучение без учителя",
            "евклидово расстояние и метрики близости",
            "простые и невыпуклые формы данных",
        ],
        "concept_uris": [
            "Root_Clustering",
            "PartitioningAlgorithm",
            "Metric_PointDistance",
            "NonFlatGeometry",
        ],
        "task_tag_slugs": ["module-1"],
        "task_slugs": [],
        "material_slugs": [
            "what-is-clustering",
            "clustering-quality-criteria",
            "distances-and-proximity",
            "feature-scaling-for-distances",
            "centroids-and-kmeans-idea",
            "data-geometry",
            "toy-cluster-shapes",
        ],
        "simulator_algorithms": [
            {"key": "kmeans", "label": "K-Means на кольцах", "preset": "circles", "module_slug": "module-1"},
        ],
        "prerequisites": [],
    },
    {
        "slug": "module-2",
        "order": 2,
        "title": "Модуль 2. Метрические алгоритмы разбиения",
        "subtitle": "K-Means",
        "summary": "От идеи центроидов к практике: классический K-Means и его быстрые расширения.",
        "highlights": [
            "шаги алгоритма Ллойда",
            "целевая функция, инерция и выбор K",
            "MiniBatch K-Means для больших данных",
            "Bisecting K-Means как нисходящий подход",
        ],
        "concept_uris": [
            "Algo_KMeans",
            "Algo_MiniBatchKMeans",
            "Algo_BisectingKMeans",
            "Param_NumClusters",
            "QualityCriterion",
            "FlatGeometry",
            "HighScalability",
            "UC_DataReduction",
        ],
        "task_tag_slugs": ["module-2"],
        "task_slugs": [],
        "material_slugs": [
            "k-means-theory",
            "kmeans-objective-and-inertia",
            "kmeans-initialization-and-limits",
            "choosing-number-of-clusters",
            "kmeans-shape-size-and-scale",
            "minibatch-kmeans-theory",
            "bisecting-kmeans-theory",
            "kmeans-as-data-reduction",
        ],
        "simulator_algorithms": [
            {"key": "kmeans", "label": "K-Means"},
            {"key": "minibatch", "label": "MiniBatch K-Means"},
            {"key": "bisecting", "label": "Bisecting K-Means"},
        ],
        "prerequisites": ["module-1"],
    },
    {
        "slug": "module-3",
        "order": 3,
        "title": "Модуль 3. Плотностные алгоритмы",
        "subtitle": "DBSCAN и соседи",
        "summary": "Невыпуклые формы, шум, выбросы и поиск плотностных областей вместо центроидов.",
        "highlights": [
            "epsilon-окрестность и ядро кластера",
            "фильтрация шума и работа с выбросами",
            "DBSCAN, FOREL и OPTICS",
        ],
        "concept_uris": [
            "Algo_DBSCAN",
            "Algo_FOREL",
            "Algo_OPTICS",
            "Algo_HDBSCAN",
        ],
        "task_tag_slugs": ["module-3"],
        "task_slugs": [],
        "material_slugs": [],
        "simulator_algorithms": [
            {"key": "dbscan", "label": "DBSCAN"},
            {"key": "forel", "label": "FOREL"},
            {"key": "optics", "label": "OPTICS"},
        ],
        "prerequisites": ["module-2"],
    },
    {
        "slug": "module-4",
        "order": 4,
        "title": "Модуль 4. Иерархические методы",
        "subtitle": "Дерево кластеров",
        "summary": "Слияние кластеров, linkage-стратегии, метод Уорда, дендрограммы и BIRCH.",
        "highlights": [
            "agglomerative clustering и linkage",
            "метод Уорда и интерпретация дендрограммы",
            "BIRCH для больших наборов данных",
        ],
        "concept_uris": [
            "Algo_Agglomerative",
            "Algo_Ward",
            "Algo_BIRCH",
        ],
        "task_tag_slugs": ["module-4"],
        "task_slugs": [],
        "material_slugs": [],
        "simulator_algorithms": [
            {"key": "agglomerative", "label": "Agglomerative"},
            {"key": "ward", "label": "Ward"},
            {"key": "birch", "label": "BIRCH"},
        ],
        "prerequisites": ["module-3"],
    },
    {
        "slug": "module-5",
        "order": 5,
        "title": "Модуль 5. Модельные и графовые методы",
        "subtitle": "GMM и спектральные подходы",
        "summary": "Вероятностная кластеризация, EM-алгоритм, графы сходства и более сложные методы.",
        "highlights": [
            "Gaussian Mixture Models и EM",
            "генерация синтетических данных через GMM",
            "Spectral Clustering и Affinity Propagation",
        ],
        "concept_uris": [
            "Algo_GaussianMixtures",
            "Algo_SpectralClustering",
            "Algo_AffinityPropagation",
        ],
        "task_tag_slugs": ["module-5"],
        "task_slugs": [],
        "material_slugs": [],
        "simulator_algorithms": [
            {"key": "gmm", "label": "GMM"},
            {"key": "spectral", "label": "Spectral"},
            {"key": "affinity", "label": "Affinity Propagation"},
        ],
        "prerequisites": ["module-4"],
    },
    {
        "slug": "module-6",
        "order": 6,
        "title": "Модуль 6. Принятие решений в кластер-анализе",
        "subtitle": "Когда какой алгоритм выбрать",
        "summary": "Метрики качества, типы вывода и выбор подхода под структуру данных и бизнес-задачу.",
        "highlights": [
            "коэффициент силуэта и оценка качества",
            "индуктивный и трансдуктивный вывод",
            "выбор алгоритма под кейс",
        ],
        "concept_uris": [
            "QMetric_SilhouetteScore",
        ],
        "task_tag_slugs": ["module-6"],
        "task_slugs": [],
        "material_slugs": [],
        "simulator_algorithms": [],
        "prerequisites": ["module-5"],
    },
]


def seed_course_modules(apps, schema_editor):
    CourseModule = apps.get_model("encyclopedia", "CourseModule")
    CourseModuleSimulator = apps.get_model("encyclopedia", "CourseModuleSimulator")
    Concept = apps.get_model("encyclopedia", "Concept")
    Material = apps.get_model("materials", "Material")
    TaskTag = apps.get_model("tasks", "TaskTag")
    Task = apps.get_model("tasks", "Task")

    modules_by_slug = {}

    for module_data in MODULES:
        module, _ = CourseModule.objects.update_or_create(
            slug=module_data["slug"],
            defaults={
                "title": module_data["title"],
                "subtitle": module_data["subtitle"],
                "summary": module_data["summary"],
                "highlights": "\n".join(module_data["highlights"]),
                "order": module_data["order"],
                "is_active": True,
            },
        )
        module.concepts.set(Concept.objects.filter(uri__in=module_data["concept_uris"]))
        module.materials.set(Material.objects.filter(slug__in=module_data["material_slugs"]))
        module.task_tags.set(TaskTag.objects.filter(slug__in=module_data["task_tag_slugs"]))
        module.tasks.set(Task.objects.filter(slug__in=module_data["task_slugs"]))

        CourseModuleSimulator.objects.filter(module=module).delete()
        for position, simulator_data in enumerate(module_data["simulator_algorithms"], start=1):
            CourseModuleSimulator.objects.create(
                module=module,
                algorithm=simulator_data["key"],
                label=simulator_data["label"],
                preset=simulator_data.get("preset", ""),
                module_slug=simulator_data.get("module_slug", ""),
                order=position,
                is_active=True,
            )

        modules_by_slug[module.slug] = module

    for module_data in MODULES:
        module = modules_by_slug[module_data["slug"]]
        prerequisites = [
            modules_by_slug[slug]
            for slug in module_data["prerequisites"]
            if slug in modules_by_slug
        ]
        module.prerequisites.set(prerequisites)


def unseed_course_modules(apps, schema_editor):
    CourseModule = apps.get_model("encyclopedia", "CourseModule")
    CourseModule.objects.filter(slug__in=[module["slug"] for module in MODULES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("encyclopedia", "0004_alter_conceptrelation_relation_type_add_recommended_after"),
        ("materials", "0002_ensure_updated_at_column"),
        ("tasks", "0005_task_related_concepts"),
    ]

    operations = [
        migrations.CreateModel(
            name="CourseModule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="Название")),
                ("slug", models.SlugField(unique=True, verbose_name="Slug")),
                ("subtitle", models.CharField(blank=True, max_length=120, verbose_name="Краткая подпись")),
                ("summary", models.TextField(blank=True, verbose_name="Описание")),
                (
                    "highlights",
                    models.TextField(
                        blank=True,
                        help_text="Один пункт на строку. Эти пункты показываются под описанием модуля.",
                        verbose_name="Ключевые пункты",
                    ),
                ),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Показывать на сайте")),
                (
                    "concepts",
                    models.ManyToManyField(
                        blank=True,
                        related_name="course_modules",
                        to="encyclopedia.concept",
                        verbose_name="Понятия",
                    ),
                ),
                (
                    "materials",
                    models.ManyToManyField(
                        blank=True,
                        related_name="course_modules",
                        to="materials.material",
                        verbose_name="Материалы",
                    ),
                ),
                (
                    "task_tags",
                    models.ManyToManyField(
                        blank=True,
                        related_name="course_modules",
                        to="tasks.tasktag",
                        verbose_name="Блоки заданий",
                    ),
                ),
                (
                    "tasks",
                    models.ManyToManyField(
                        blank=True,
                        related_name="course_modules",
                        to="tasks.task",
                        verbose_name="Отдельные задания",
                    ),
                ),
                (
                    "prerequisites",
                    models.ManyToManyField(
                        blank=True,
                        related_name="dependent_modules",
                        symmetrical=False,
                        to="encyclopedia.coursemodule",
                        verbose_name="Предыдущие модули",
                    ),
                ),
            ],
            options={
                "verbose_name": "Модуль курса",
                "verbose_name_plural": "Модули курса",
                "ordering": ["order", "title"],
            },
        ),
        migrations.CreateModel(
            name="CourseModuleSimulator",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("algorithm", models.CharField(max_length=50, verbose_name="Алгоритм")),
                ("label", models.CharField(max_length=120, verbose_name="Подпись")),
                ("preset", models.CharField(blank=True, max_length=80, verbose_name="Preset")),
                (
                    "module_slug",
                    models.SlugField(
                        blank=True,
                        help_text="Оставьте пустым, чтобы использовать slug текущего модуля.",
                        verbose_name="Slug модуля для прогресса",
                    ),
                ),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Показывать")),
                (
                    "module",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="simulator_items",
                        to="encyclopedia.coursemodule",
                        verbose_name="Модуль",
                    ),
                ),
            ],
            options={
                "verbose_name": "Симулятор модуля",
                "verbose_name_plural": "Симуляторы модулей",
                "ordering": ["module__order", "order", "label"],
            },
        ),
        migrations.AddConstraint(
            model_name="coursemodulesimulator",
            constraint=models.UniqueConstraint(
                fields=("module", "algorithm", "preset", "module_slug"),
                name="unique_simulator_step_per_module",
            ),
        ),
        migrations.RunPython(seed_course_modules, unseed_course_modules),
    ]
