from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import Material, MaterialProgress


def materials_list(request):
    """Список учебных материалов."""
    materials = list(Material.objects.order_by('order', 'title'))
    progress_map = {}

    if request.user.is_authenticated and materials:
        progress_map = {
            progress.material_id: progress
            for progress in MaterialProgress.objects.filter(
                user=request.user,
                material_id__in=[material.id for material in materials],
            )
        }

    for material in materials:
        material_progress = progress_map.get(material.id)
        material.is_opened = bool(material_progress and material_progress.first_opened_at)
        material.is_completed = bool(material_progress and material_progress.completed_at)

    return render(request, 'materials/materials_list.html', {'materials': materials})


def material_detail(request, slug):
    """Детальная страница материала."""
    material = get_object_or_404(Material, slug=slug)
    progress = None

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f"{reverse('core:login')}?next={request.path}")

        progress, _ = MaterialProgress.objects.get_or_create(user=request.user, material=material)
        action = request.POST.get('action')

        if action == 'mark_completed':
            now = timezone.now()
            if not progress.first_opened_at:
                progress.first_opened_at = now
            progress.last_opened_at = now
            progress.completed_at = now
            progress.open_count = max(progress.open_count, 1)
            progress.save(update_fields=['first_opened_at', 'last_opened_at', 'completed_at', 'open_count'])
            messages.success(request, 'Материал отмечен как изученный.')
        elif action == 'mark_uncompleted':
            progress.completed_at = None
            progress.save(update_fields=['completed_at'])
            messages.success(request, 'Отметка изучения снята.')

        return redirect(material.get_absolute_url())

    if request.user.is_authenticated:
        progress, _ = MaterialProgress.objects.get_or_create(user=request.user, material=material)
        now = timezone.now()
        update_fields = ['last_opened_at', 'open_count']

        if not progress.first_opened_at:
            progress.first_opened_at = now
            update_fields.append('first_opened_at')

        progress.last_opened_at = now
        progress.open_count += 1
        progress.save(update_fields=update_fields)

    return render(request, 'materials/material_detail.html', {'material': material, 'progress': progress})
