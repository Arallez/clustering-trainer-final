from django.contrib import admin
from .models import Task, TaskTag, UserTaskAttempt
from .forms import TaskAdminForm
from apps.core.admin_site import admin_site, CustomModelAdminMixin


class TaskTagAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order',)


class TaskAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    form = TaskAdminForm
    change_form_template = 'admin/tasks/task/change_form.html'
    list_display = ('title', 'task_type', 'tags', 'difficulty', 'order')
    list_filter = ('tags', 'task_type', 'difficulty', 'concept', 'related_concepts')
    search_fields = ('title', 'description', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('tags__order', 'order')
    filter_horizontal = ('related_concepts',)
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'description', 'task_type', 'difficulty', 'tags', 'order', 'concept', 'related_concepts')}),
        ('Код (для типа «Написание кода»)', {'fields': ('function_name', 'initial_code', 'solution_code'), 'classes': ('collapse',)}),
        ('Данные теста (JSON)', {'fields': ('test_input', 'expected_output'), 'classes': ('collapse',), 'description': 'Заполняются автоматически из конструктора для тестов.'}),
    )

    def _build_quiz_questions_list(self, test_input, expected_output):
        ti = test_input or {}
        eo = expected_output
        expected_list = eo if isinstance(eo, list) else ([eo] if eo else [])
        questions_data = (ti or {}).get("questions")
        if questions_data:
            return [
                {
                    "question": q.get("question", ""),
                    "options": q.get("options", []),
                    "correct": expected_list[i] if i < len(expected_list) else "",
                }
                for i, q in enumerate(questions_data)
            ]
        if "question" in ti or "options" in ti:
            return [{"question": ti.get("question", ""), "options": ti.get("options", []), "correct": expected_list[0] if expected_list else (str(eo) if eo else "")}]
        return []

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_quiz_constructor'] = True
        extra_context['quiz_questions'] = []
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, object_id)
        # Всегда показываем конструктор, JavaScript скроет его если тип != 'choice'
        extra_context['show_quiz_constructor'] = True
        if obj and obj.task_type == 'choice':
            extra_context['quiz_questions'] = self._build_quiz_questions_list(obj.test_input, obj.expected_output)
        else:
            extra_context['quiz_questions'] = []
        return super().change_view(request, object_id, form_url, extra_context)


class UserTaskAttemptAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ('user', 'task', 'is_correct', 'created_at')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('user__username', 'task__title')
    readonly_fields = ('code', 'error_message', 'created_at')


# Регистрируем в кастомной админке
admin_site.register(TaskTag, TaskTagAdmin)
admin_site.register(Task, TaskAdmin)
admin_site.register(UserTaskAttempt, UserTaskAttemptAdmin)
