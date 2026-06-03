import secrets
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def generate_join_code():
    """Генерирует уникальный код подключения к группе (8 символов)."""
    return secrets.token_hex(4).upper()


class TeacherProfile(models.Model):
    """Профиль преподавателя — пользователи с такой записью могут создавать группы и тесты."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Преподаватель'
        verbose_name_plural = 'Преподаватели'

    def __str__(self):
        return self.user.get_username()


class StudentGroup(models.Model):
    """Учебная группа. Студенты подключаются по коду."""
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_groups')
    name = models.CharField(max_length=200, verbose_name='Название группы')
    join_code = models.CharField(max_length=16, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return f"{self.name} ({self.join_code})"

    def save(self, *args, **kwargs):
        if not self.join_code:
            self.join_code = generate_join_code()
            while StudentGroup.objects.filter(join_code=self.join_code).exists():
                self.join_code = generate_join_code()
        super().save(*args, **kwargs)


class GroupMembership(models.Model):
    """Участие студента в группе."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE, related_name='members')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'group')]
        verbose_name = 'Участник группы'
        verbose_name_plural = 'Участники групп'

    def __str__(self):
        return f"{self.user.username} в {self.group.name}"


# --- БАНК ВОПРОСОВ И ЗАДАНИЙ (ТЕСТИРОВАНИЕ) ---

class Question(models.Model):
    """
    Вопрос/Задание в банке преподавателя.
    Студент может ответить текстом/кодом и/или прикрепить файл.
    """
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_bank', verbose_name='Автор')
    title = models.CharField(max_length=250, verbose_name='Краткое название (тема)')
    content = models.TextField(verbose_name='Текст задания / Условие', help_text="Поддерживается разметка Markdown, сырой HTML и формулы KaTeX ($...$, $$...$$). Преобразуется в HTML на стороне клиента.")
    max_score = models.PositiveIntegerField(default=10, verbose_name='Максимальный балл')
    attached_file = models.FileField(upload_to='teacher_materials/', blank=True, null=True, verbose_name='Прикрепленный материал для студента (CSV, PDF и т.д.)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Вопрос / Задание'
        verbose_name_plural = 'Банк вопросов'

    def __str__(self):
        return f"[{self.teacher.username}] {self.title} (Max: {self.max_score})"


class Test(models.Model):
    """Тест/Контрольная работа: собирается из вопросов банка."""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_tests')
    group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE, related_name='tests')
    title = models.CharField(max_length=200, verbose_name='Название теста')

    questions = models.ManyToManyField(
        Question,
        related_name='tests',
        blank=True,
        verbose_name='Ручные вопросы из банка'
    )
    tasks = models.ManyToManyField(
        'tasks.Task',
        related_name='testing_tests',
        blank=True,
        through='TestTask',
        verbose_name='Автопроверяемые задания курса'
    )
    auto_task_score = models.PositiveIntegerField(
        default=1,
        verbose_name='Баллов за автозадание'
    )
    time_limit_minutes = models.PositiveIntegerField(
        default=60,
        verbose_name='Лимит времени (минут)'
    )
    opens_at = models.DateTimeField(verbose_name='Открывается')
    closes_at = models.DateTimeField(verbose_name='Закрывается')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Тест (Контрольная)'
        verbose_name_plural = 'Тесты (Контрольные)'

    def __str__(self):
        return f"{self.title} ({self.group.name})"

    def is_active(self):
        now = timezone.now()
        return self.opens_at <= now <= self.closes_at

    def is_future(self):
        return timezone.now() < self.opens_at

    def is_past(self):
        return timezone.now() > self.closes_at

    @property
    def max_possible_score(self):
        manual_score = sum(q.max_score for q in self.questions.all())
        auto_score = sum(item.score for item in self.test_tasks.all())
        return manual_score + auto_score


class TestTask(models.Model):
    """Автопроверяемое задание внутри контрольной с отдельным весом и порядком."""
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='test_tasks')
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE, related_name='test_assignments')
    score = models.PositiveIntegerField(default=1, verbose_name='Баллов за задание')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        db_table = 'testing_test_tasks'
        ordering = ['order', 'task__tags__order', 'task__order', 'task__title']
        unique_together = [('test', 'task')]
        verbose_name = 'Автозадание в контрольной'
        verbose_name_plural = 'Автозадания в контрольных'

    def __str__(self):
        return f"{self.test.title}: {self.task.title} ({self.score})"


class TestAttempt(models.Model):
    """Попытка прохождения контрольной работы целиком."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_attempts')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Новые поля для статуса проверки
    is_graded = models.BooleanField(default=False, verbose_name='Проверено преподавателем')
    total_score = models.PositiveIntegerField(default=0, verbose_name='Итоговый балл')
    teacher_comment = models.TextField(blank=True, null=True, verbose_name='Общий комментарий к работе')

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Попытка прохождения'
        verbose_name_plural = 'Попытки прохождения'
        unique_together = [('user', 'test')]

    def __str__(self):
        status = 'Проверено' if self.is_graded else ('Сдано на проверку' if self.submitted_at else 'В процессе')
        return f"{self.user.username} — {self.test.title} ({status})"

    @property
    def is_submitted(self):
        return self.submitted_at is not None


class StudentAnswer(models.Model):
    """
    Ответ студента на конкретный вопрос в рамках попытки.
    Преподаватель может оценить этот конкретный ответ и оставить обратную связь.
    """
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers')
    
    # Ответ студента (текст/код ИЛИ прикрепленный файл)
    text_answer = models.TextField(blank=True, null=True, verbose_name='Текстовый ответ / Код студента')
    file_answer = models.FileField(upload_to='student_answers/', blank=True, null=True, verbose_name='Загруженный файл ответа')
    
    answered_at = models.DateTimeField(auto_now=True)
    
    # Оценка преподавателя
    score = models.PositiveIntegerField(null=True, blank=True, verbose_name='Выставленный балл')
    feedback = models.TextField(blank=True, null=True, verbose_name='Обратная связь (комментарий преподавателя)')

    class Meta:
        unique_together = [('attempt', 'question')]
        verbose_name = 'Ответ студента'
        verbose_name_plural = 'Ответы студентов'

    def __str__(self):
        return f"Ответ {self.attempt.user.username} на '{self.question.title}'"
