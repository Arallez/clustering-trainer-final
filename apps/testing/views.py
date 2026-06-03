from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlencode
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from zoneinfo import ZoneInfo

from apps.tasks.models import Task, UserTaskAttempt
from .models import TeacherProfile, StudentGroup, GroupMembership, Test, TestTask, TestAttempt, Question, StudentAnswer

def is_teacher(user):
    if not user.is_authenticated:
        return False
    return hasattr(user, 'teacher_profile') and user.teacher_profile is not None


def calculate_attempt_progress(attempt):
    """Вычисляет прогресс попытки теста (сколько вопросов отвечено)."""
    test = attempt.test
    questions = test.questions.all()
    tasks = test.tasks.all()
    total = questions.count() + tasks.count()
    if total == 0:
        return {
            'total': 0,
            'attempted': 0,
            'percent': 0,
            'question_statuses': {},
            'task_statuses': {},
            'correct_auto_tasks': 0,
        }

    answers = StudentAnswer.objects.filter(attempt=attempt)
    answered_q_ids = set(a.question_id for a in answers if a.text_answer or a.file_answer)

    task_attempts = UserTaskAttempt.objects.filter(test_attempt=attempt)
    attempted_task_ids = set(task_attempts.values_list('task_id', flat=True))
    correct_task_ids = set(task_attempts.filter(is_correct=True).values_list('task_id', flat=True))

    attempted = len(answered_q_ids) + len(attempted_task_ids)
    percent = int((attempted / total) * 100) if total > 0 else 0

    question_statuses = {}
    for q in questions:
        question_statuses[q.id] = 'attempted' if q.id in answered_q_ids else 'not_attempted'

    task_statuses = {}
    for task in tasks:
        if task.id in correct_task_ids:
            task_statuses[task.id] = 'correct'
        elif task.id in attempted_task_ids:
            task_statuses[task.id] = 'attempted'
        else:
            task_statuses[task.id] = 'not_attempted'

    return {
        'total': total,
        'attempted': attempted,
        'percent': percent,
        'question_statuses': question_statuses,
        'task_statuses': task_statuses,
        'correct_auto_tasks': len(correct_task_ids),
    }


def get_latest_auto_task_attempts(attempt):
    """Возвращает последнюю попытку по каждому автозаданию внутри контрольной."""
    latest_attempts = []
    seen_task_ids = set()
    score_by_task_id = {
        assignment.task_id: assignment.score
        for assignment in attempt.test.test_tasks.all()
    }
    queryset = (
        UserTaskAttempt.objects.filter(test_attempt=attempt)
        .select_related('task', 'task__tags', 'task__concept')
        .order_by('task__tags__order', 'task__order', 'task__title', '-is_correct', '-created_at')
    )
    for task_attempt in queryset:
        if task_attempt.task_id in seen_task_ids:
            continue
        task_attempt.test_score = score_by_task_id.get(task_attempt.task_id, attempt.test.auto_task_score)
        latest_attempts.append(task_attempt)
        seen_task_ids.add(task_attempt.task_id)
    return latest_attempts


def build_task_picker_groups():
    tasks = Task.objects.select_related('tags', 'concept').order_by('tags__order', 'order', 'title')
    groups = []
    current_key = object()
    current_group = None

    for task in tasks:
        tag = task.tags
        key = tag.id if tag else None
        if key != current_key:
            current_group = {
                'title': tag.name if tag else 'Без блока',
                'slug': tag.slug if tag else 'untagged',
                'tasks': [],
            }
            groups.append(current_group)
            current_key = key
        current_group['tasks'].append(task)

    return groups


def testing_home(request):
    """Главная вкладки «Тестирование»."""
    if not request.user.is_authenticated:
        messages.warning(
            request,
            'Тестирование доступно только зарегистрированным пользователям. Войдите или зарегистрируйтесь.'
        )
        return redirect(reverse('core:login') + '?' + urlencode({'next': request.get_full_path()}))
    
    user = request.user
    teacher = is_teacher(user)

    if teacher:
        groups = StudentGroup.objects.filter(teacher=user).prefetch_related('members')
        tests = Test.objects.filter(owner=user).select_related('group').prefetch_related('questions', 'test_tasks')
        questions = Question.objects.filter(teacher=user)
        return render(request, 'testing/teacher_home.html', {
            'groups': groups,
            'tests': tests,
            'questions': questions
        })

    # Студент: группы, в которых состоит, и все тесты по ним
    memberships = GroupMembership.objects.filter(user=user).select_related('group')
    group_ids = [m.group_id for m in memberships]
    now = timezone.now()
    all_tests = []
    if group_ids:
        all_tests = list(
            Test.objects.filter(group_id__in=group_ids)
            .select_related('group')
            .prefetch_related('questions', 'test_tasks')
            .order_by('-opens_at')
        )
    
    tests_with_status = []
    for t in all_tests:
        if t.opens_at <= now <= t.closes_at:
            status = 'active'
        elif now < t.opens_at:
            status = 'future'
        else:
            status = 'past'
        tests_with_status.append({'test': t, 'status': status})
    
    my_attempts = TestAttempt.objects.filter(user=user).select_related('test')
    attempts_with_progress = []
    for attempt in my_attempts:
        progress = calculate_attempt_progress(attempt)
        # Вычисляем процент и статус для проверенных работ
        score_percent = None
        score_status = None
        if attempt.is_graded and attempt.test.max_possible_score > 0:
            score_percent = round((attempt.total_score / attempt.test.max_possible_score) * 100)
            if score_percent < 40:
                score_status = 'failed'
            elif score_percent < 81:
                score_status = 'passed'
            else:
                score_status = 'excellent'
        attempts_with_progress.append({
            'attempt': attempt,
            'progress': progress,
            'score_percent': score_percent,
            'score_status': score_status,
        })

    return render(request, 'testing/student_home.html', {
        'memberships': memberships,
        'tests_with_status': tests_with_status,
        'attempts_with_progress': attempts_with_progress,
    })


@login_required
def join_group(request):
    """Подключиться к группе по коду."""
    if request.method == 'POST':
        code = (request.POST.get('join_code') or '').strip().upper()
        if not code:
            messages.error(request, 'Введите код группы.')
            return redirect('testing:home')
        group = StudentGroup.objects.filter(join_code=code).first()
        if not group:
            messages.error(request, 'Группа с таким кодом не найдена.')
            return redirect('testing:home')
        _, created = GroupMembership.objects.get_or_create(user=request.user, group=group)
        if created:
            messages.success(request, f'Вы подключились к группе «{group.name}».')
        else:
            messages.info(request, f'Вы уже в группе «{group.name}».')
        return redirect('testing:home')
    return redirect('testing:home')


@login_required
def create_group(request):
    """Создать группу (только преподаватель)."""
    if not is_teacher(request.user):
        return redirect('testing:home')
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        if name:
            group = StudentGroup.objects.create(teacher=request.user, name=name)
            messages.success(request, f'Группа «{group.name}» создана.')
    return redirect('testing:home')


@login_required
def delete_group(request, group_id):
    """Удалить группу (только преподаватель)."""
    if not is_teacher(request.user):
        return redirect('testing:home')
    group = get_object_or_404(StudentGroup, pk=group_id, teacher=request.user)
    if request.method == 'POST':
        group_name = group.name
        group.delete()
        messages.success(request, f'Группа «{group_name}» успешно удалена.')
    return redirect('testing:home')


@login_required
def group_detail(request, group_id):
    """Подробная информация о группе."""
    if not is_teacher(request.user):
        return redirect('testing:home')
        
    group = get_object_or_404(StudentGroup, pk=group_id, teacher=request.user)
    memberships = group.members.select_related('user').all()
    users = [m.user for m in memberships]
    tests = group.tests.prefetch_related('questions', 'test_tasks').order_by('-created_at')
    attempts = TestAttempt.objects.filter(test__in=tests, user__in=users).select_related('user', 'test')
    
    student_rows = []
    for u in users:
        row = {'user': u, 'test_results': []}
        for t in tests:
            attempt_obj = next((a for a in attempts if a.user_id == u.id and a.test_id == t.id), None)
            progress = calculate_attempt_progress(attempt_obj) if attempt_obj else None
            row['test_results'].append({'test': t, 'attempt': attempt_obj, 'progress': progress})
        student_rows.append(row)
            
    return render(request, 'testing/group_detail.html', {
        'group': group,
        'tests': tests,
        'student_rows': student_rows
    })

# --- НОВЫЕ ВЬЮХИ ДЛЯ РАБОТЫ С ВОПРОСАМИ ---

@login_required
def create_question(request):
    """Создание вопроса в банке (преподаватель)."""
    if not is_teacher(request.user):
        return redirect('testing:home')
        
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        score = request.POST.get('max_score', 10)
        attached_file = request.FILES.get('attached_file')
        
        Question.objects.create(
            teacher=request.user,
            title=title,
            content=content,
            max_score=int(score),
            attached_file=attached_file
        )
        messages.success(request, 'Вопрос добавлен в банк.')
        return redirect('testing:home')
        
    return render(request, 'testing/create_question.html')

@login_required
def question_detail(request, question_id):
    """Просмотр задания на отдельной странице."""
    if not is_teacher(request.user):
        return redirect('testing:home')
        
    question = get_object_or_404(Question, pk=question_id, teacher=request.user)
    return render(request, 'testing/question_detail.html', {'question': question})

@login_required
def delete_question(request, question_id):
    """Удалить вопрос из банка (преподаватель)."""
    if not is_teacher(request.user):
        return redirect('testing:home')
    
    question = get_object_or_404(Question, pk=question_id, teacher=request.user)
    if request.method == 'POST':
        title = question.title
        question.delete()
        messages.success(request, f'Вопрос «{title}» удален.')
    
    return redirect('testing:home')


@login_required
def delete_test(request, test_id):
    """Удалить тест (преподаватель)."""
    if not is_teacher(request.user):
        return redirect('testing:home')
    
    test = get_object_or_404(Test, pk=test_id, owner=request.user)
    if request.method == 'POST':
        title = test.title
        test.delete()
        messages.success(request, f'Тест «{title}» удален.')
    
    return redirect('testing:home')

@login_required
def create_test(request):
    """Создать тест из вопросов банка."""
    if not is_teacher(request.user):
        return redirect('testing:home')
        
    groups = StudentGroup.objects.filter(teacher=request.user)
    questions = Question.objects.filter(teacher=request.user)
    task_groups = build_task_picker_groups()
    
    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        group_id = request.POST.get('group')
        time_limit = request.POST.get('time_limit_minutes') or 60
        auto_task_score = request.POST.get('auto_task_score') or 1
        opens_at = request.POST.get('opens_at')
        closes_at = request.POST.get('closes_at')
        question_ids = request.POST.getlist('questions')
        task_ids = request.POST.getlist('tasks')
        try:
            time_limit = max(1, int(time_limit))
        except (TypeError, ValueError):
            time_limit = 60
        try:
            auto_task_score = max(1, int(auto_task_score))
        except (TypeError, ValueError):
            auto_task_score = 1
        
        if not title or not group_id or (not question_ids and not task_ids):
            messages.error(request, 'Укажите название, группу и выберите хотя бы один ручной вопрос или автозадание.')
            return render(request, 'testing/create_test.html', {'groups': groups, 'questions': questions, 'task_groups': task_groups})
            
        group = get_object_or_404(StudentGroup, pk=group_id, teacher=request.user)
        
        # Обработка дат (оставляем старую логику)
        tz_name = getattr(settings, 'TEST_DATETIME_TIMEZONE', None) or settings.TIME_ZONE
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo('UTC')
            
        if opens_at:
            try:
                opens_at = datetime.strptime(opens_at, '%Y-%m-%dT%H:%M')
                if timezone.is_naive(opens_at):
                    opens_at = timezone.make_aware(opens_at, tz)
            except ValueError:
                opens_at = timezone.now()
        else:
            opens_at = timezone.now()
            
        if closes_at:
            try:
                closes_at = datetime.strptime(closes_at, '%Y-%m-%dT%H:%M')
                if timezone.is_naive(closes_at):
                    closes_at = timezone.make_aware(closes_at, tz)
            except ValueError:
                closes_at = opens_at + timedelta(days=1)
        else:
            closes_at = opens_at + timedelta(days=1)

        test = Test.objects.create(
            owner=request.user,
            group=group,
            title=title,
            time_limit_minutes=time_limit,
            auto_task_score=auto_task_score,
            opens_at=opens_at,
            closes_at=closes_at,
        )
        test.questions.set(Question.objects.filter(pk__in=question_ids, teacher=request.user))
        selected_tasks = list(Task.objects.filter(pk__in=task_ids))
        task_by_id = {str(task.id): task for task in selected_tasks}
        assignments = []
        for default_order, task_id in enumerate(task_ids, start=1):
            task = task_by_id.get(str(task_id))
            if not task:
                continue
            score_value = request.POST.get(f'task_score_{task_id}') or auto_task_score
            order_value = request.POST.get(f'task_order_{task_id}') or default_order
            try:
                score_value = max(1, int(score_value))
            except (TypeError, ValueError):
                score_value = auto_task_score
            try:
                order_value = max(0, int(order_value))
            except (TypeError, ValueError):
                order_value = default_order
            assignments.append(TestTask(test=test, task=task, score=score_value, order=order_value))
        TestTask.objects.bulk_create(assignments)
        messages.success(request, f'Тест «{test.title}» создан.')
        return redirect('testing:home')
        
    return render(request, 'testing/create_test.html', {'groups': groups, 'questions': questions, 'task_groups': task_groups})


@login_required
def start_test(request, test_id):
    """Начать тест (студент)."""
    test = get_object_or_404(Test, pk=test_id)
    if not test.is_active():
        messages.error(request, 'Этот тест сейчас недоступен.')
        return redirect('testing:home')
    if not GroupMembership.objects.filter(user=request.user, group=test.group).exists():
        messages.error(request, 'Вы не в группе этого теста.')
        return redirect('testing:home')
        
    attempt, created = TestAttempt.objects.get_or_create(user=request.user, test=test)
    if not created and attempt.submitted_at:
        return redirect('testing:attempt_result', attempt_id=attempt.pk)
    return redirect('testing:take_test', attempt_id=attempt.pk)


@login_required
def take_test(request, attempt_id):
    """Прохождение теста (отображение всех вопросов на одной странице)."""
    attempt = get_object_or_404(TestAttempt, pk=attempt_id, user=request.user)
    test = attempt.test
    
    if attempt.submitted_at:
        return redirect('testing:attempt_result', attempt_id=attempt.pk)

    deadline = min(attempt.started_at + timedelta(minutes=test.time_limit_minutes), test.closes_at)
    if timezone.now() > deadline:
        attempt.submitted_at = attempt.submitted_at or deadline
        attempt.save(update_fields=['submitted_at'])
        messages.error(request, 'Время теста истекло. Работа автоматически закрыта.')
        return redirect('testing:attempt_result', attempt_id=attempt.pk)

    if not test.is_active():
        messages.error(request, 'Время теста истекло.')
        return redirect('testing:home')
    
    questions = test.questions.all()
    auto_assignments = list(
        test.test_tasks.select_related('task', 'task__concept', 'task__tags')
        .order_by('order', 'task__tags__order', 'task__order', 'task__title')
    )
    
    existing_answers = {a.question_id: a for a in StudentAnswer.objects.filter(attempt=attempt)}
    latest_task_attempts = {}
    for task_attempt in UserTaskAttempt.objects.filter(test_attempt=attempt).order_by('-created_at'):
        latest_task_attempts.setdefault(task_attempt.task_id, task_attempt)

    for assignment in auto_assignments:
        task_attempt = latest_task_attempts.get(assignment.task_id)
        assignment.latest_test_attempt = task_attempt
        assignment.test_status = 'correct' if task_attempt and task_attempt.is_correct else ('attempted' if task_attempt else 'not_attempted')
    
    if request.method == 'POST':
        for q in questions:
            ans, _ = StudentAnswer.objects.get_or_create(attempt=attempt, question=q)
            text_val = request.POST.get(f'q_{q.id}_text', '')
            ans.text_answer = text_val

            file_upload = request.FILES.get(f'q_{q.id}_file')
            if file_upload:
                ans.file_answer = file_upload
                
            ans.save()
            
        # Если нажата кнопка завершения теста
        if 'submit_test' in request.POST:
            attempt.submitted_at = timezone.now()
            attempt.save()
            messages.success(request, 'Ответы сохранены. Тест сдан на проверку.')
            return redirect('testing:attempt_result', attempt_id=attempt.pk)
        else:
            messages.success(request, 'Черновик ответов сохранен.')
            return redirect('testing:take_test', attempt_id=attempt.pk)
            
    return render(request, 'testing/take_test.html', {
        'attempt': attempt,
        'test': test,
        'questions': questions,
        'auto_assignments': auto_assignments,
        'existing_answers': existing_answers,
        'ends_at': deadline,
    })


@login_required
def attempt_result(request, attempt_id):
    """Результат попытки для студента."""
    attempt = get_object_or_404(TestAttempt, pk=attempt_id, user=request.user)
    answers = StudentAnswer.objects.filter(attempt=attempt).select_related('question')
    auto_task_attempts = get_latest_auto_task_attempts(attempt)
    
    # Вычисляем процент и статус
    score_percent = None
    score_status = None
    if attempt.is_graded and attempt.test.max_possible_score > 0:
        score_percent = round((attempt.total_score / attempt.test.max_possible_score) * 100)
        if score_percent < 40:
            score_status = 'failed'  # красный, тест завален
        elif score_percent < 81:
            score_status = 'passed'  # желтый, тест сдан
        else:
            score_status = 'excellent'  # зеленый, отлично сдан
    
    return render(request, 'testing/attempt_result.html', {
        'attempt': attempt,
        'answers': answers,
        'auto_task_attempts': auto_task_attempts,
        'score_percent': score_percent,
        'score_status': score_status,
    })


@login_required
def test_results(request, test_id):
    """Результаты теста для преподавателя (список сдач)."""
    test = get_object_or_404(Test, pk=test_id)
    if test.owner_id != request.user.pk:
        return redirect('testing:home')
    
    attempts = TestAttempt.objects.filter(test=test).select_related('user').order_by('-started_at')
    
    attempts_data = []
    for att in attempts:
        # Вычисляем процент и статус для проверенных работ
        score_percent = None
        score_status = None
        if att.is_graded and test.max_possible_score > 0:
            score_percent = round((att.total_score / test.max_possible_score) * 100)
            if score_percent < 40:
                score_status = 'failed'
            elif score_percent < 81:
                score_status = 'passed'
            else:
                score_status = 'excellent'
        attempts_data.append({
            'attempt': att,
            'progress': calculate_attempt_progress(att),
            'score_percent': score_percent,
            'score_status': score_status,
        })
    
    return render(request, 'testing/test_results.html', {
        'test': test,
        'attempts_data': attempts_data
    })

@login_required
def grade_attempt(request, attempt_id):
    """Страница проверки конкретной работы преподавателем."""
    attempt = get_object_or_404(TestAttempt, pk=attempt_id)
    if attempt.test.owner_id != request.user.pk:
        return redirect('testing:home')
    if not attempt.submitted_at:
        messages.error(request, 'Работа ещё не сдана студентом.')
        return redirect('testing:test_results', test_id=attempt.test_id)
        
    answers = StudentAnswer.objects.filter(attempt=attempt).select_related('question')
    auto_task_attempts = get_latest_auto_task_attempts(attempt)
    
    if request.method == 'POST':
        total_score = 0
        for ans in answers:
            score_val = request.POST.get(f'score_{ans.id}')
            feedback_val = request.POST.get(f'feedback_{ans.id}')
            if score_val:
                try:
                    ans.score = min(max(int(score_val), 0), ans.question.max_score)
                except (TypeError, ValueError):
                    ans.score = 0
                total_score += ans.score
            ans.feedback = feedback_val
            ans.save()

        correct_task_ids = set(
            UserTaskAttempt.objects.filter(test_attempt=attempt, is_correct=True)
            .values_list('task_id', flat=True)
        )
        total_score += sum(
            assignment.score
            for assignment in attempt.test.test_tasks.all()
            if assignment.task_id in correct_task_ids
        )
            
        attempt.total_score = total_score
        attempt.teacher_comment = request.POST.get('teacher_comment', '')
        attempt.is_graded = True
        attempt.save()
        messages.success(request, f'Работа проверена. Итоговый балл: {total_score}')
        return redirect('testing:test_results', test_id=attempt.test_id)
        
    return render(request, 'testing/grade_attempt.html', {
        'attempt': attempt,
        'answers': answers,
        'auto_task_attempts': auto_task_attempts,
    })
