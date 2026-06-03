from django.db import models
from django.conf import settings


class SimulatorProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='simulator_progress')
    module_slug = models.SlugField(verbose_name="Модуль курса")
    algorithm = models.CharField(max_length=64, verbose_name="Алгоритм")
    preset = models.CharField(max_length=64, blank=True, verbose_name="Датасет")
    run_count = models.PositiveIntegerField(default=0, verbose_name="Количество запусков")
    first_run_at = models.DateTimeField(null=True, blank=True, verbose_name="Первый запуск")
    last_run_at = models.DateTimeField(null=True, blank=True, verbose_name="Последний запуск")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Засчитано")

    class Meta:
        ordering = ['-last_run_at', '-completed_at']
        verbose_name = "Прогресс по симулятору"
        verbose_name_plural = "Прогресс по симулятору"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'module_slug', 'algorithm', 'preset'],
                name='unique_user_simulator_progress',
            ),
        ]

    def __str__(self):
        preset = f" / {self.preset}" if self.preset else ""
        return f"{self.user} -> {self.module_slug}: {self.algorithm}{preset}"
