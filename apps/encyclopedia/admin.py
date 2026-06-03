from django import forms
from django.contrib import admin
from django.core.cache import cache
from .models import Concept, ConceptRelation, CourseModule, CourseModuleSimulator
from apps.core.admin_site import admin_site, CustomModelAdminMixin


# Ключ кэша графа онтологии
GRAPH_CACHE_KEY = 'ontology_graph_data'


class ConceptAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'uri', 'created_at')
    search_fields = ('title', 'description')

    def delete_queryset(self, request, queryset):
        """Массовое удаление - очищаем кэш после."""
        super().delete_queryset(request, queryset)
        cache.delete(GRAPH_CACHE_KEY)


class ConceptRelationAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ('source', 'relation_type', 'target')
    list_filter = ('relation_type',)
    autocomplete_fields = ['source', 'target']

    def delete_queryset(self, request, queryset):
        """Массовое удаление - очищаем кэш после."""
        super().delete_queryset(request, queryset)
        cache.delete(GRAPH_CACHE_KEY)


class CourseModuleAdminForm(forms.ModelForm):
    class Meta:
        model = CourseModule
        fields = "__all__"
        help_texts = {
            "title": "Основное название блока в учебном маршруте.",
            "slug": "Технический ключ для якорей страницы. Обычно заполняется автоматически из названия.",
            "subtitle": "Короткая подпись для компактных карточек. Можно оставить пустой.",
            "summary": "Описание модуля, которое студент видит на странице учебного маршрута.",
            "highlights": "Ключевые пункты модуля. Каждый пункт пишется с новой строки.",
            "order": "Чем меньше число, тем выше модуль в учебном маршруте.",
            "is_active": "Если выключить, модуль не будет показываться студентам.",
            "concepts": (
                "Понятия онтологии, которые относятся к модулю. По ним система может подтянуть "
                "материалы и задания, а также считать прогресс по концептам."
            ),
            "materials": (
                "Материалы, которые нужно явно показать внутри модуля. Материалы также могут "
                "попасть в модуль через выбранные понятия."
            ),
            "task_tags": "Блоки заданий из банка курса. Удобно выбирать, когда в модуль входит целая группа задач.",
            "tasks": "Отдельные задания для точечного добавления.",
            "prerequisites": "Предыдущие модули маршрута. Это связь порядка изучения, а не ручной процент прогресса.",
        }


class CourseModuleAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    form = CourseModuleAdminForm
    list_display = ("title", "subtitle", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "subtitle", "summary", "slug")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("concepts", "materials", "task_tags", "tasks", "prerequisites")
    ordering = ("order", "title")
    fieldsets = (
        (
            "1. Основная информация",
            {
                "fields": (
                    "title",
                    "slug",
                    "subtitle",
                    "summary",
                    "highlights",
                    "order",
                    "is_active",
                ),
                "description": (
                    "Эти поля отвечают за то, как модуль выглядит в учебном маршруте. "
                    "Статус и процент прохождения руками не задаются: они считаются автоматически."
                ),
            },
        ),
        (
            "2. Состав модуля",
            {
                "fields": (
                    "concepts",
                    "materials",
                    "task_tags",
                    "tasks",
                ),
                "description": (
                    "Здесь задается, что входит в модуль: понятия, теория и практические задания. "
                    "Если выбрать понятия, система дополнительно подберет связанные с ними материалы и задачи."
                ),
            },
        ),
        (
            "3. Связи маршрута",
            {
                "fields": (
                    "prerequisites",
                ),
                "description": (
                    "Эти связи описывают порядок обучения между модулями. Они не заменяют связи онтологии, "
                    "а помогают выстроить учебный маршрут."
                ),
            },
        ),
    )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        field = super().formfield_for_manytomany(db_field, request, **kwargs)
        if db_field.name == "task_tags":
            field.label = "Блоки заданий"
            field.help_text = (
                'Выберите группы заданий, которые должны отображаться внутри этого модуля. '
                'Новые группы создаются в разделе "Теги заданий".'
            )
        elif db_field.name == "tasks":
            field.label = "Отдельные задания"
            field.help_text = "Используйте для точечного добавления задач, которые не входят в выбранные блоки."
        elif db_field.name == "prerequisites":
            field.label = "Предыдущие модули"
            field.help_text = "Модули, которые логически идут перед текущим."
        return field


class CourseModuleSimulatorAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ("label", "module", "algorithm_name", "preset_name", "order", "is_active")
    list_filter = ("module", "algorithm", "is_active")
    search_fields = ("label", "algorithm", "preset", "module__title", "module__slug")
    ordering = ("module__order", "order", "label")
    fields = ("module", "algorithm", "label", "preset", "order", "is_active")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "algorithm":
            field.label = "Алгоритм симулятора"
            field.help_text = "Выберите готовый алгоритм. Технический ключ подставится автоматически."
        elif db_field.name == "label":
            field.label = "Название ссылки"
            field.help_text = "Так ссылка будет называться в модуле курса."
        elif db_field.name == "preset":
            field.help_text = "Можно оставить пустым. Если выбрать набор, симулятор откроется с готовыми точками."
        return field

    @admin.display(description="Алгоритм", ordering="algorithm")
    def algorithm_name(self, obj):
        return obj.get_algorithm_display()

    @admin.display(description="Набор данных", ordering="preset")
    def preset_name(self, obj):
        return obj.get_preset_display()


# Регистрируем в кастомной админке
admin_site.register(Concept, ConceptAdmin)
admin_site.register(ConceptRelation, ConceptRelationAdmin)
admin_site.register(CourseModule, CourseModuleAdmin)
admin_site.register(CourseModuleSimulator, CourseModuleSimulatorAdmin)
