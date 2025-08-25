from django.conf import settings
from django.db import models
from django.urls import reverse
from apps.companies.models import Company


CATEGORIES = [
    ("logistics", "Logistics/Drivers"),
    ("retail", "Retail/HORECA"),
    ("cs_bpo", "Customer Support/BPO"),
    ("trades", "Blue-collar Trades"),
    ("it", "IT/Tech"),
]

CITIES = [
    ("bucharest", "București"),
    ("cluj", "Cluj-Napoca"),
    ("iasi", "Iași"),
    ("timisoara", "Timișoara"),
    ("brasov", "Brașov"),
]


class Job(models.Model):
    company = models.ForeignKey(Company, related_name="jobs", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    category = models.CharField(max_length=32, choices=CATEGORIES)
    city = models.CharField(max_length=64, choices=CITIES)
    description = models.TextField()
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="posted_jobs"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["category", "city", "is_active"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} @ {self.company.name}"

    def get_absolute_url(self):
        return reverse("jobs:detail", args=[self.slug])


class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    applicant_name = models.CharField(max_length=255)
    applicant_email = models.EmailField()
    cover_letter = models.TextField()
    resume = models.FileField(upload_to='resumes/')
    submitted_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Application for {self.job.title} by {self.applicant_name}"

