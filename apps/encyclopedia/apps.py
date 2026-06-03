from django.apps import AppConfig

class EncyclopediaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.encyclopedia'
    verbose_name = 'База Знаний (Онтология)'

    def ready(self):
        """Подключение сигналов при запуске приложения."""
        import apps.encyclopedia.signals  # noqa: F401
