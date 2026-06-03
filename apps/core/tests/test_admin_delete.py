from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.testing.models import StudentGroup


@override_settings(ALLOWED_HOSTS=["127.0.0.1", "localhost", "testserver"])
class AdminDeleteFlowTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin_delete_case",
            email="admin@example.com",
            password="pass12345",
        )
        self.teacher = User.objects.create_user(
            username="teacher_delete_case",
            password="pass12345",
        )
        self.auth_group = Group.objects.create(name="Delete Me Group")
        self.student_group = StudentGroup.objects.create(
            name="Delete Me Student Group",
            teacher=self.teacher,
        )

        self.client.force_login(self.admin_user)

    def test_auth_group_bulk_delete_uses_builtin_action_name(self):
        changelist_url = reverse("admin:auth_group_changelist")

        response = self.client.post(
            changelist_url,
            {
                "action": "delete_selected",
                "_selected_action": [str(self.auth_group.pk)],
                "select_across": "0",
            },
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="action" value="delete_selected"', html=False)

        response = self.client.post(
            changelist_url,
            {
                "action": "delete_selected",
                "_selected_action": [str(self.auth_group.pk)],
                "select_across": "0",
                "post": "yes",
            },
            HTTP_HOST="127.0.0.1",
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Group.objects.filter(pk=self.auth_group.pk).exists())

    def test_student_group_bulk_delete_uses_custom_action_name(self):
        changelist_url = reverse("admin:testing_studentgroup_changelist")

        response = self.client.post(
            changelist_url,
            {
                "action": "delete_selected_custom",
                "_selected_action": [str(self.student_group.pk)],
                "select_across": "0",
            },
            HTTP_HOST="127.0.0.1",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="action" value="delete_selected_custom"', html=False)

        response = self.client.post(
            changelist_url,
            {
                "action": "delete_selected_custom",
                "_selected_action": [str(self.student_group.pk)],
                "select_across": "0",
                "post": "yes",
            },
            HTTP_HOST="127.0.0.1",
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(StudentGroup.objects.filter(pk=self.student_group.pk).exists())

    def test_user_single_delete_still_works(self):
        delete_url = reverse("admin:auth_user_delete", args=[self.teacher.pk])

        response = self.client.post(
            delete_url,
            {"post": "yes"},
            HTTP_HOST="127.0.0.1",
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(pk=self.teacher.pk).exists())
