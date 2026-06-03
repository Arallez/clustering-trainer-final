# Симулятор — только песочница. Админка заданий в apps.tasks.

from django.contrib import admin

from .models import SimulatorProgress


@admin.register(SimulatorProgress)
class SimulatorProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'module_slug', 'algorithm', 'preset', 'run_count', 'completed_at', 'last_run_at')
    list_filter = ('module_slug', 'algorithm', 'preset', 'completed_at')
    search_fields = ('user__username', 'module_slug', 'algorithm', 'preset')
    readonly_fields = ('first_run_at', 'last_run_at', 'completed_at', 'run_count')
