import secrets
import string

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from apps.testing.models import TeacherProfile


class Command(BaseCommand):
    help = "Создаёт пользователя-преподавателя с TeacherProfile и is_staff=True."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="teacher1")
        parser.add_argument("--email", default="teacher1@example.com")
        parser.add_argument("--first-name", default="Преподаватель")
        parser.add_argument("--last-name", default="Тестовый")
        parser.add_argument("--password", default=None)

    def handle(self, *args, **opts):
        username = opts["username"]
        password = opts["password"] or "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(12)
        )

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": opts["email"],
                "first_name": opts["first_name"],
                "last_name": opts["last_name"],
                "is_staff": True,
            },
        )
        user.email = opts["email"]
        user.first_name = opts["first_name"]
        user.last_name = opts["last_name"]
        user.is_staff = True
        user.set_password(password)
        user.save()

        TeacherProfile.objects.get_or_create(user=user)

        self.stdout.write(self.style.SUCCESS("Преподаватель готов:"))
        self.stdout.write(f"  username: {username}")
        self.stdout.write(f"  password: {password}")
        self.stdout.write(f"  email:    {opts['email']}")
        self.stdout.write(f"  created:  {created}")
