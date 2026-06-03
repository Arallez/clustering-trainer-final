from django.contrib import admin
from django.urls import reverse

from apps.core.admin_site import CustomModelAdminMixin, admin_site

from .models import Material, MaterialProgress


class MaterialAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'concept', 'order')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order', 'title')
    search_fields = ('title', 'content')
    list_filter = ('concept',)
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'content', 'order', 'concept')}),
    )
    change_list_template = 'admin/change_list.html'
    change_form_template = 'admin/change_form.html'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            'has_add_permission': self.has_add_permission(request),
            'add_url': reverse(f'{self.admin_site.name}:{self.opts.app_label}_{self.opts.model_name}_add'),
            'verbose_name': self.opts.verbose_name,
            'verbose_name_plural': self.opts.verbose_name_plural,
        })
        return super().changelist_view(request, extra_context)


admin_site.register(Material, MaterialAdmin)


@admin.register(MaterialProgress, site=admin_site)
class MaterialProgressAdmin(CustomModelAdminMixin, admin.ModelAdmin):
    list_display = ('user', 'material', 'open_count', 'last_opened_at', 'completed_at')
    list_select_related = ('user', 'material')
    search_fields = ('user__username', 'material__title', 'material__slug')
    list_filter = ('completed_at',)
    ordering = ('-last_opened_at',)
