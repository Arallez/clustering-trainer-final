"""
Кастомный AdminSite с современным дизайном.
"""
from django.contrib import messages
from django.contrib.admin import AdminSite
from django.contrib.admin.utils import get_deleted_objects
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class CustomAdminSite(AdminSite):
    site_header = _('Clustering Trainer Administration')
    site_title = _('Admin Panel')
    index_title = _('Панель управления')
    site_url = '/'

    def _get_user_initials(self, user):
        if user.first_name:
            initials = user.first_name[0].upper()
            if user.last_name:
                initials += user.last_name[0].upper()
            return initials
        return user.username[0:2].upper() if len(user.username) >= 2 else user.username.upper()

    def _get_admin_counts(self):
        try:
            from apps.encyclopedia.models import Concept, ConceptRelation, CourseModule, CourseModuleSimulator
            from apps.materials.models import Material
            from apps.tasks.models import Task, TaskTag
            from apps.testing.models import Question, StudentGroup, Test

            return {
                'materials_count': Material.objects.count(),
                'tasks_count': Task.objects.count(),
                'task_tags_count': TaskTag.objects.count(),
                'tests_count': Test.objects.count(),
                'questions_count': Question.objects.count(),
                'groups_count': StudentGroup.objects.count(),
                'concepts_count': Concept.objects.count(),
                'relations_count': ConceptRelation.objects.count(),
                'course_modules_count': CourseModule.objects.count(),
                'course_module_simulators_count': CourseModuleSimulator.objects.count(),
                'users_count': User.objects.count(),
                'auth_groups_count': Group.objects.count(),
            }
        except Exception:
            return {
                'materials_count': 0,
                'tasks_count': 0,
                'task_tags_count': 0,
                'tests_count': 0,
                'questions_count': 0,
                'groups_count': 0,
                'concepts_count': 0,
                'relations_count': 0,
                'course_modules_count': 0,
                'course_module_simulators_count': 0,
                'users_count': 0,
                'auth_groups_count': 0,
            }

    def each_context(self, request):
        context = super().each_context(request)
        context.update({
            'site_home_url': reverse('core:home'),
            'user_initials': self._get_user_initials(request.user),
            'admin_urls': {
                'index': reverse(f'{self.name}:index'),
                'logout': reverse(f'{self.name}:logout'),
                'materials_changelist': reverse(f'{self.name}:materials_material_changelist'),
                'materials_add': reverse(f'{self.name}:materials_material_add'),
                'tasks_changelist': reverse(f'{self.name}:tasks_task_changelist'),
                'tasks_add': reverse(f'{self.name}:tasks_task_add'),
                'task_tags_changelist': reverse(f'{self.name}:tasks_tasktag_changelist'),
                'tests_changelist': reverse(f'{self.name}:testing_test_changelist'),
                'tests_add': reverse(f'{self.name}:testing_test_add'),
                'questions_changelist': reverse(f'{self.name}:testing_question_changelist'),
                'groups_changelist': reverse(f'{self.name}:testing_studentgroup_changelist'),
                'concepts_changelist': reverse(f'{self.name}:encyclopedia_concept_changelist'),
                'relations_changelist': reverse(f'{self.name}:encyclopedia_conceptrelation_changelist'),
                'course_modules_changelist': reverse(f'{self.name}:encyclopedia_coursemodule_changelist'),
                'course_modules_add': reverse(f'{self.name}:encyclopedia_coursemodule_add'),
                'course_module_simulators_changelist': reverse(
                    f'{self.name}:encyclopedia_coursemodulesimulator_changelist'
                ),
                'course_module_simulators_add': reverse(f'{self.name}:encyclopedia_coursemodulesimulator_add'),
                'users_changelist': reverse(f'{self.name}:auth_user_changelist'),
                'auth_groups_changelist': reverse(f'{self.name}:auth_group_changelist'),
            },
        })
        context.update(self._get_admin_counts())
        return context

    def index(self, request, extra_context=None):
        context = {
            **self.each_context(request),
            'title': self.index_title,
            **(extra_context or {}),
        }
        return TemplateResponse(request, 'admin/index.html', context)


class CustomModelAdminMixin:
    """
    Mixin для ModelAdmin с кастомными шаблонами удаления.
    """

    actions = ['delete_selected_custom']

    def delete_selected_custom(self, request, queryset):
        """
        Кастомный action для массового удаления с нашим шаблоном.
        """
        from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME

        selected = request.POST.getlist(ACTION_CHECKBOX_NAME)

        if not selected:
            return HttpResponseRedirect(request.get_full_path())

        if request.POST.get('post') == 'yes':
            if not self.has_delete_permission(request):
                raise PermissionDenied

            count = queryset.count()
            queryset.delete()

            self.message_user(
                request,
                _(f'Успешно удалено {count} записей.'),
                messages.SUCCESS,
            )

            post_url = reverse(
                f'{self.admin_site.name}:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist'
            )
            return HttpResponseRedirect(post_url)

        opts = self.model._meta
        deleted_objects, model_count, perms_needed, protected = get_deleted_objects(
            list(queryset), request, self.admin_site
        )

        context = {
            **self.admin_site.each_context(request),
            'title': _('Подтверждение удаления'),
            'queryset': queryset,
            'selected_count': len(selected),
            'opts': opts,
            'deletable_objects': dict(model_count) if model_count else {},
            'perms_lacking': perms_needed,
            'protected': protected,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
        }

        return TemplateResponse(
            request,
            'admin/delete_selected_confirmation.html',
            context,
        )

    delete_selected_custom.short_description = 'Удалить выбранные записи'
    delete_selected_custom.allowed_permissions = ('delete',)

    def delete_view(self, request, object_id, extra_context=None):
        """
        Кастомное представление для удаления одного объекта.
        """
        obj = self.get_object(request, object_id)

        if not self.has_delete_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise PermissionDenied

        deleted_objects, model_count, perms_needed, protected = get_deleted_objects(
            [obj], request, self.admin_site
        )

        if request.POST and 'post' in request.POST:
            if perms_needed:
                raise PermissionDenied

            obj.delete()

            self.message_user(request, _('Объект успешно удалён.'), messages.SUCCESS)

            post_url = reverse(
                f'{self.admin_site.name}:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist'
            )
            return HttpResponseRedirect(post_url)

        context = {
            **self.admin_site.each_context(request),
            'title': _('Удаление'),
            'object': obj,
            'original': obj,
            'deleted_objects': deleted_objects,
            'desc': dict(model_count) if model_count else {},
            'perms_lacking': perms_needed,
            'protected': protected,
            'opts': self.model._meta,
            'is_popup': False,
            'has_delete_permission': self.has_delete_permission(request, obj),
            **(extra_context or {}),
        }

        return TemplateResponse(request, 'admin/delete_confirmation.html', context)


admin_site = CustomAdminSite(name='admin')
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
