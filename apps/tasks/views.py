import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import Task, TaskTag, UserTaskAttempt
from .sandbox import evaluate_code_submission
from apps.encyclopedia.curriculum import build_curriculum_modules
from apps.encyclopedia.recommendations import get_task_remediation, is_task_available


def task_list(request):
    tags = TaskTag.objects.prefetch_related('tasks').order_by('order')
    uncategorized = Task.objects.filter(tags__isnull=True).order_by('order')
    completed_task_ids = set()
    available_task_ids = set(Task.objects.values_list('id', flat=True))
    blocked_tasks_info = {}
    
    if request.user.is_authenticated:
        completed_task_ids = set(
            UserTaskAttempt.objects.filter(user=request.user, is_correct=True).values_list('task_id', flat=True)
        )
    
    return render(request, 'tasks/task_list.html', {
        'tags': tags,
        'uncategorized': uncategorized,
        'completed_task_ids': completed_task_ids,
        'available_task_ids': available_task_ids,
        'blocked_tasks_info': blocked_tasks_info,
        'curriculum_modules': build_curriculum_modules(request.user if request.user.is_authenticated else None),
    })


@ensure_csrf_cookie
def challenge_detail(request, slug):
    task = get_object_or_404(Task, slug=slug)
    previous_code = ""
    test_attempt_id = None
    is_available = True
    missing_concepts = []
    required_materials = []
    
    if request.user.is_authenticated:
        last_attempt = request.user.task_attempts.filter(task=task, is_correct=True).first()
        if last_attempt:
            previous_code = last_attempt.code
        ta_id = request.GET.get('test_attempt')
        if ta_id:
            from apps.testing.models import TestAttempt
            ta = TestAttempt.objects.filter(pk=ta_id, user=request.user).first()
            if ta and not ta.submitted_at:
                test_attempt_id = ta.pk
        
        # Проверяем доступность задачи на основе онтологии
        if task.concept:
            _, missing_concepts = is_task_available(request.user, task)
            if missing_concepts:
                from apps.materials.models import Material
                required_materials = Material.objects.filter(concept__in=missing_concepts)
    
    return render(request, 'tasks/challenge_detail.html', {
        'task': task,
        'previous_code': previous_code or task.initial_code,
        'test_attempt_id': test_attempt_id,
        'is_available': is_available,
        'missing_concepts': missing_concepts,
        'required_materials': required_materials,
    })


def check_solution(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    try:
        data = json.loads(request.body)
        slug = data.get('slug') or data.get('task_slug')
        user_input = data.get('code')
        test_attempt_id = data.get('test_attempt_id')
        task = get_object_or_404(Task, slug=slug)
        is_correct = False
        result_details = {}
        error_msg = None

        if task.task_type == 'choice':
            expected = task.expected_output
            if isinstance(user_input, list) and isinstance(expected, list):
                is_correct = user_input == expected
                result_details = {'quiz_results': [
                    i < len(user_input) and user_input[i] == expected[i] for i in range(len(expected))
                ]}
            else:
                is_correct = (str(user_input).strip() == str(expected).strip())
            if not is_correct:
                error_msg = "Некоторые ответы неверны." if isinstance(expected, list) else f"Выбрано: {user_input}."
        else:
            outcome = evaluate_code_submission(user_input, task)
            is_correct = outcome.is_correct
            # Если sandbox не запустил код (security/syntax/sandbox-ошибка) —
            # трактуем как неверное решение, чтобы попытка сохранилась
            # и студент получил рекомендации материалов для повторения.
            error_msg = outcome.error_message if not is_correct else None

        if request.user.is_authenticated:
            code_to_save = json.dumps(user_input, ensure_ascii=False) if isinstance(user_input, (list, dict)) else str(user_input)
            test_attempt = None
            if test_attempt_id:
                from apps.testing.models import TestAttempt
                ta = TestAttempt.objects.filter(pk=test_attempt_id, user=request.user).first()
                if ta and not ta.submitted_at:
                    test_attempt = ta
            UserTaskAttempt.objects.create(
                user=request.user, task=task, code=code_to_save, is_correct=is_correct,
                error_message=error_msg, test_attempt=test_attempt,
            )
        response_data = {'success': is_correct, 'correct': is_correct}
        if is_correct:
            response_data['message'] = 'Правильно!'
        else:
            response_data['error'] = error_msg
            response_data['remediation'] = get_task_remediation(request.user, task)
        response_data.update(result_details)
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
