from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    class Roles(models.TextChoices):
        SEEKER = "seeker", "Seeker"
        EMPLOYER = "employer", "Employer"

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.SEEKER)
    phone = models.CharField(max_length=32, blank=True)

    def __str__(self):
        return self.get_username()


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="profile", on_delete=models.CASCADE)
    city = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    cv = models.FileField(upload_to="cvs/", blank=True, null=True)
    receive_alerts = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile({self.user.username})"