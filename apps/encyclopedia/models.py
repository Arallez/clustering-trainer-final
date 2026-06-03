from django.db import models


class Concept(models.Model):
    """
    Ontology node materialized in Django.
    Stores an individual concept, algorithm, metric, parameter, or another
    domain element imported from the OWL model.
    """

    uri = models.CharField(max_length=255, unique=True, help_text="Unique ID from OWL ontology")
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание (Markdown)", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Понятие"
        verbose_name_plural = "Понятия"


class ConceptRelation(models.Model):
    """
    Semantic edge between two ontology concepts.
    """

    RELATION_TYPES = [
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
    ]

    source = models.ForeignKey(
        Concept,
        on_delete=models.CASCADE,
        related_name="relations_out",
        verbose_name="Откуда",
    )
    target = models.ForeignKey(
        Concept,
        on_delete=models.CASCADE,
        related_name="relations_in",
        verbose_name="Куда",
    )
    relation_type = models.CharField(max_length=30, choices=RELATION_TYPES, verbose_name="Тип связи")

    def __str__(self):
        return f"{self.source} -> [{self.relation_type}] -> {self.target}"

    class Meta:
        verbose_name = "Семантическая связь"
        verbose_name_plural = "Связи"
        unique_together = ("source", "target", "relation_type")


class CourseModule(models.Model):
    """
    Editable curriculum block shown in the learning path and task list.
    """

    title = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    subtitle = models.CharField(max_length=120, blank=True, verbose_name="Краткая подпись")
    summary = models.TextField(blank=True, verbose_name="Описание")
    highlights = models.TextField(
        blank=True,
        verbose_name="Ключевые пункты",
        help_text="Один пункт на строку. Эти пункты показываются под описанием модуля.",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Показывать на сайте")
    concepts = models.ManyToManyField(
        Concept,
        blank=True,
        related_name="course_modules",
        verbose_name="Понятия",
    )
    materials = models.ManyToManyField(
        "materials.Material",
        blank=True,
        related_name="course_modules",
        verbose_name="Материалы",
    )
    task_tags = models.ManyToManyField(
        "tasks.TaskTag",
        blank=True,
        related_name="course_modules",
        verbose_name="Блоки заданий",
    )
    tasks = models.ManyToManyField(
        "tasks.Task",
        blank=True,
        related_name="course_modules",
        verbose_name="Отдельные задания",
    )
    prerequisites = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="dependent_modules",
        verbose_name="Предыдущие модули",
    )

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Модуль курса"
        verbose_name_plural = "Модули курса"

    def __str__(self):
        return self.title

    def get_highlights(self):
        return [line.strip() for line in self.highlights.splitlines() if line.strip()]


class CourseModuleSimulator(models.Model):
    """
    Simulator step attached to a curriculum module.
    """

    ALGORITHM_CHOICES = [
        ("kmeans", "K-Means"),
        ("minibatch", "MiniBatch K-Means"),
        ("bisecting", "Bisecting K-Means"),
        ("dbscan", "DBSCAN"),
        ("forel", "FOREL"),
        ("optics", "OPTICS"),
        ("meanshift", "Mean Shift"),
        ("agglomerative", "Agglomerative Clustering"),
        ("ward", "Ward"),
        ("birch", "BIRCH"),
        ("gmm", "Gaussian Mixture Models"),
        ("spectral", "Spectral Clustering"),
        ("affinity", "Affinity Propagation"),
    ]

    PRESET_CHOICES = [
        ("", "Без стартового набора"),
        ("blobs", "Облака"),
        ("moons", "Луны"),
        ("circles", "Кольца"),
        ("grid", "Сетка"),
        ("hierarchy", "Иерархия кластеров"),
        ("dense_sparse", "Плотный и разреженный кластеры"),
        ("anisotropic", "Вытянутые группы"),
        ("outliers", "Шум и выбросы"),
        ("many_blobs", "Много групп"),
        ("bridge", "Мост между группами"),
    ]

    module = models.ForeignKey(
        CourseModule,
        on_delete=models.CASCADE,
        related_name="simulator_items",
        verbose_name="Модуль",
    )
    algorithm = models.CharField(
        max_length=50,
        choices=ALGORITHM_CHOICES,
        verbose_name="Алгоритм",
    )
    label = models.CharField(max_length=120, verbose_name="Название ссылки")
    preset = models.CharField(
        max_length=80,
        blank=True,
        choices=PRESET_CHOICES,
        verbose_name="Стартовый набор данных",
    )
    module_slug = models.SlugField(
        blank=True,
        verbose_name="Slug модуля для прогресса",
        help_text="Оставьте пустым, чтобы использовать slug текущего модуля.",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Показывать")

    class Meta:
        ordering = ["module__order", "order", "label"]
        verbose_name = "Симулятор модуля"
        verbose_name_plural = "Симуляторы модулей"
        constraints = [
            models.UniqueConstraint(
                fields=["module", "algorithm", "preset", "module_slug"],
                name="unique_simulator_step_per_module",
            )
        ]

    def __str__(self):
        return f"{self.module}: {self.label}"

    def get_progress_module_slug(self):
        return self.module_slug or self.module.slug
