from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    experience_points = models.IntegerField(default=0)
    current_level = models.IntegerField(default=1)

    def __str__(self):
        return f"Profile of {self.user.username}"
