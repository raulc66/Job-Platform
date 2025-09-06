from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SeekerProfile  # import lazily if you have circulars

User = get_user_model()


@receiver(post_save, sender=User)
def ensure_seeker_profile(sender, instance, created, **kwargs):
    if created:
        SeekerProfile.objects.get_or_create(user=instance)