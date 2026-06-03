from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from apps.encyclopedia.models import Concept


class Material(models.Model):
    """
    Theoretical material or article linked to an ontology Concept.
    """

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    slug = models.SlugField(unique=True, verbose_name="URL Slug")
    content = models.TextField(
        verbose_name="Содержание (Markdown)",
        help_text="Поддерживается разметка Markdown, сырой HTML и формулы KaTeX ($...$, $$...$$). Преобразуется в HTML на стороне клиента.",
    )
    concept = models.ForeignKey(
        Concept,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='materials',
        verbose_name="Связанный концепт",
    )
    order = models.IntegerField(default=0, verbose_name="Порядок (сортировка)")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        db_table = 'core_material'
        ordering = ['order', 'title']
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('materials:material_detail', kwargs={'slug': self.slug})


class MaterialProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='material_progress')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='progress_entries')
    first_opened_at = models.DateTimeField(null=True, blank=True, verbose_name="Первое открытие")
    last_opened_at = models.DateTimeField(null=True, blank=True, verbose_name="Последнее открытие")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Отмечен как изученный")
    open_count = models.PositiveIntegerField(default=0, verbose_name="Количество открытий")

    class Meta:
        db_table = 'core_materialprogress'
        ordering = ['-last_opened_at', '-completed_at']
        verbose_name = "Прогресс по материалу"
        verbose_name_plural = "Прогресс по материалам"
        constraints = [
            models.UniqueConstraint(fields=['user', 'material'], name='unique_user_material_progress'),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.material.title}"
