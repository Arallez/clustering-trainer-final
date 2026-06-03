from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q, Prefetch
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.html import strip_tags
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from .forms import UserRegisterForm
from apps.tasks.models import Task, UserTaskAttempt, TaskTag
from apps.materials.models import Material, MaterialProgress
from apps.encyclopedia.recommendations import (
    get_recommended_tasks,
    get_recommended_materials,
    get_user_progress
)
from apps.testing.models import TeacherProfile


@method_decorator(ensure_csrf_cookie, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class AccountLoginView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True


@method_decorator(never_cache, name='dispatch')
class AccountLogoutView(LogoutView):
    next_page = reverse_lazy('core:home')


def csrf_failure(request, reason=''):
    """
    Показываем пользователю нормальный путь восстановления вместо debug-страницы 403.
    Чаще всего это происходит после смены аккаунта, когда форма была открыта со старым CSRF-токеном.
    """
    messages.warning(
        request,
        'Сессия обновилась. Страница перезагружена, повторите действие еще раз.',
        fail_silently=True,
    )

    if request.user.is_authenticated:
        if request.path == reverse('core:login') or request.path == reverse('core:logout'):
            return redirect('core:profile')

        referer = request.META.get('HTTP_REFERER')
        if referer and url_has_allowed_host_and_scheme(
            referer,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(referer)

        return redirect('core:profile')

    if request.path == reverse('core:register'):
        return redirect('core:register')

    return redirect('core:login')


def home(request):
    return render(request, 'core/home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            
            # Send Welcome Email
            try:
                subject = 'Добро пожаловать в Clustering Trainer!'
                html_message = render_to_string('emails/welcome.html', {
                    'username': username,
                    'simulator_url': request.build_absolute_uri(reverse('simulator:index')),
                })
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject,
                    plain_message,
                    None, # Uses DEFAULT_FROM_EMAIL
                    [email],
                    html_message=html_message,
                    fail_silently=True # Don't crash if email fails
                )
            except Exception as e:
                print(f"Error sending email: {e}")

            messages.success(request, f'Создан аккаунт для {username}! Письмо отправлено на почту.')
            return redirect('core:login')
    else:
        form = UserRegisterForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def profile(request):
    user = request.user
    
    # 1. Общая статистика
    total_tasks = Task.objects.count()
    
    # Количество уникальных решенных задач (где is_correct=True)
    solved_tasks_count = UserTaskAttempt.objects.filter(
        user=user, 
        is_correct=True
    ).values('task').distinct().count()
    
    # Прогресс в процентах
    task_progress_percent = int((solved_tasks_count / total_tasks * 100)) if total_tasks > 0 else 0
    
    # 2. История последних действий (последние 10 попыток)
    recent_attempts = UserTaskAttempt.objects.filter(user=user).select_related('task')[:10]
    
    # 3. Адаптивные рекомендации на основе онтологии
    recommended_tasks = get_recommended_tasks(user, limit=5)
    recommended_materials = get_recommended_materials(user, limit=5)
    ontology_progress = get_user_progress(user)
    total_materials = Material.objects.count()
    completed_materials_count = MaterialProgress.objects.filter(
        user=user,
        completed_at__isnull=False,
    ).count()
    
    # Проверяем, является ли пользователь преподавателем
    is_teacher = hasattr(user, 'teacher_profile')
    
    context = {
        'user': user,
        'total_tasks': total_tasks,
        'solved_tasks_count': solved_tasks_count,
        'task_progress_percent': task_progress_percent,
        'overall_progress_percent': ontology_progress['progress_percent'],
        'recent_attempts': recent_attempts,
        'recommended_tasks': recommended_tasks,
        'recommended_materials': recommended_materials,
        'ontology_progress': ontology_progress,
        'is_teacher': is_teacher,
        'total_materials': total_materials,
        'completed_materials_count': completed_materials_count,
    }
    
    return render(request, 'core/profile.html', context)
