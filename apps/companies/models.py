from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Company(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="companies", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    website = models.URLField(blank=True)
    city = models.CharField(max_length=120, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:240]
        super().save(*args, **kwargs)