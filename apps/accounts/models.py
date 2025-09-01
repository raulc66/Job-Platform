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


class SeekerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seekerprofile")
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=255, blank=True)
    skills = models.TextField(blank=True, help_text="Lista de aptitudini separate prin virgule")
    portfolio_url = models.URLField(blank=True, null=True)  # optional
    quick_apply_ready = models.BooleanField(default=False)

    def skills_list(self):
        return [s.strip() for s in (self.skills or "").split(",") if s.strip()]

    def __str__(self):
        return f"SeekerProfile({self.user_id})"