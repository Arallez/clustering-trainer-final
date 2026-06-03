from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.encyclopedia.models import Concept
from apps.tasks.models import Task, UserTaskAttempt
from apps.testing.models import (
    GroupMembership,
    Question,
    StudentAnswer,
    StudentGroup,
    TeacherProfile,
    Test,
    TestAttempt,
    TestTask,
)
from apps.testing.views import calculate_attempt_progress


class TestingWorkflowTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teacher", password="pass")
        self.student = User.objects.create_user(username="student", password="pass")
        TeacherProfile.objects.create(user=self.teacher)

    def test_teacher_creates_group_and_student_joins_by_code(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("testing:create_group"), {"name": "ПР-1"})

        self.assertEqual(response.status_code, 302)
        group = StudentGroup.objects.get(name="ПР-1")
        self.assertEqual(group.teacher, self.teacher)
        self.assertTrue(group.join_code)

        self.client.force_login(self.student)
        response = self.client.post(
            reverse("testing:join_group"),
            {"join_code": group.join_code.lower()},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            GroupMembership.objects.filter(user=self.student, group=group).exists()
        )

        self.client.post(reverse("testing:join_group"), {"join_code": group.join_code})
        self.assertEqual(
            GroupMembership.objects.filter(user=self.student, group=group).count(),
            1,
        )

    def test_teacher_creates_test_from_manual_question_and_auto_task(self):
        group = StudentGroup.objects.create(teacher=self.teacher, name="ПР-2")
        question = Question.objects.create(
            teacher=self.teacher,
            title="Theory",
            content="Explain clustering.",
            max_score=7,
        )
        concept = Concept.objects.create(uri="concept:kmeans", title="K-Means")
        task = Task.objects.create(
            title="Auto task",
            slug="auto-task",
            description="",
            concept=concept,
            function_name="solve",
        )

        self.client.force_login(self.teacher)
        response = self.client.post(
            reverse("testing:create_test"),
            {
                "title": "Control work",
                "group": group.id,
                "time_limit_minutes": "45",
                "auto_task_score": "2",
                "opens_at": "2026-01-01T10:00",
                "closes_at": "2026-01-02T10:00",
                "questions": [str(question.id)],
                "tasks": [str(task.id)],
                f"task_score_{task.id}": "5",
                f"task_order_{task.id}": "3",
            },
        )

        self.assertEqual(response.status_code, 302)
        test = Test.objects.get(title="Control work")
        self.assertEqual(test.questions.get(), question)
        assignment = TestTask.objects.get(test=test, task=task)
        self.assertEqual(assignment.score, 5)
        self.assertEqual(assignment.order, 3)

    def test_attempt_progress_counts_manual_answers_and_auto_tasks(self):
        group = StudentGroup.objects.create(teacher=self.teacher, name="ПР-3")
        GroupMembership.objects.create(user=self.student, group=group)
        question = Question.objects.create(
            teacher=self.teacher,
            title="Theory",
            content="Explain clustering.",
            max_score=7,
        )
        task = Task.objects.create(
            title="Auto task",
            slug="auto-progress-task",
            description="",
            function_name="solve",
        )
        now = timezone.now()
        test = Test.objects.create(
            owner=self.teacher,
            group=group,
            title="Progress test",
            opens_at=now,
            closes_at=now + timezone.timedelta(days=1),
        )
        test.questions.add(question)
        TestTask.objects.create(test=test, task=task, score=5, order=1)
        attempt = TestAttempt.objects.create(user=self.student, test=test)
        StudentAnswer.objects.create(
            attempt=attempt,
            question=question,
            text_answer="Answer",
        )
        UserTaskAttempt.objects.create(
            user=self.student,
            task=task,
            code="def solve(): pass",
            is_correct=True,
            test_attempt=attempt,
        )

        progress = calculate_attempt_progress(attempt)

        self.assertEqual(progress["total"], 2)
        self.assertEqual(progress["attempted"], 2)
        self.assertEqual(progress["percent"], 100)
        self.assertEqual(progress["correct_auto_tasks"], 1)
