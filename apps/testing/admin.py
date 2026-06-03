from django.contrib import admin
from .models import TeacherProfile, StudentGroup, GroupMembership, Question, Test, TestTask, TestAttempt, StudentAnswer
from apps.core.admin_site import admin_site, CustomModelAdminMixin


class TeacherProfileAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


class StudentGroupAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'teacher', 'join_code', 'created_at')
    search_fields = ('name', 'teacher__username', 'join_code')
    readonly_fields = ('join_code',)


class GroupMembershipAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ('user', 'group', 'joined_at')
    list_filter = ('group',)


class QuestionAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'teacher', 'max_score')
    list_filter = ('teacher',)


class TestAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'owner', 'group', 'opens_at', 'closes_at')
    list_filter = ('owner', 'group')
    filter_horizontal = ('questions',)


class TestTaskAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ('test', 'task', 'score', 'order')
    list_filter = ('test', 'task__tags')
    search_fields = ('test__title', 'task__title', 'task__slug')


class TestAttemptAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ('user', 'test', 'started_at', 'submitted_at', 'is_graded', 'total_score')
    list_filter = ('is_graded', 'test')


class StudentAnswerAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ('attempt', 'question', 'score')


# Регистрируем в кастомной админке
admin_site.register(TeacherProfile, TeacherProfileAdmin)
admin_site.register(StudentGroup, StudentGroupAdmin)
admin_site.register(GroupMembership, GroupMembershipAdmin)
admin_site.register(Question, QuestionAdmin)
admin_site.register(Test, TestAdmin)
admin_site.register(TestTask, TestTaskAdmin)
admin_site.register(TestAttempt, TestAttemptAdmin)
admin_site.register(StudentAnswer, StudentAnswerAdmin)
