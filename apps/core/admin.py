from django.contrib import admin

from .admin_site import CustomModelAdminMixin, admin_site
from .models import UserProfile


class UserProfileAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ("user", "experience_points", "current_level")
    search_fields = ("user__username", "user__email")
    ordering = ("user__username",)


admin_site.register(UserProfile, UserProfileAdmin)
