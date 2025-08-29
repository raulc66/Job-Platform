from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

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

    MOD_PENDING = "pending"
    MOD_APPROVED = "approved"
    MOD_REJECTED = "rejected"
    MODERATION_CHOICES = [
        (MOD_PENDING, "În așteptare"),
        (MOD_APPROVED, "Aprobat"),
        (MOD_REJECTED, "Respins"),
    ]
    moderation_status = models.CharField(max_length=20, choices=MODERATION_CHOICES, default=MOD_APPROVED)
    flagged_reason = models.CharField(max_length=120, blank=True)
    flagged_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["category", "city", "is_active"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} @ {self.company.name}"

    def get_absolute_url(self):
        return reverse("jobs:detail", kwargs={"slug": self.slug})

    def approve(self):
        self.moderation_status = self.MOD_APPROVED
        self.approved_at = timezone.now()
        # Activate if model has is_active
        if "is_active" in {f.name for f in self._meta.get_fields()}:
            self.is_active = True
        self.save(update_fields=["moderation_status", "approved_at"] + (["is_active"] if hasattr(self, "is_active") else []))

    def reject(self, reason: str = ""):
        self.moderation_status = self.MOD_REJECTED
        if reason and not self.flagged_reason:
            self.flagged_reason = reason[:120]
            self.flagged_at = timezone.now()
        if "is_active" in {f.name for f in self._meta.get_fields()}:
            self.is_active = False
        self.save(update_fields=["moderation_status", "flagged_reason", "flagged_at"] + (["is_active"] if hasattr(self, "is_active") else []))


class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    applicant_name = models.CharField(max_length=255)
    applicant_email = models.EmailField()
    cover_letter = models.TextField()
    resume = models.FileField(upload_to='resumes/')
    submitted_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Application for {self.job.title} by {self.applicant_name}"


class JobQuestion(models.Model):
    TYPE_YESNO = "yes_no"
    TYPE_TEXT = "short_text"
    TYPE_NUMBER = "number"
    TYPE_CHOICES = [
        (TYPE_YESNO, "Da/Nu"),
        (TYPE_TEXT, "Răspuns scurt"),
        (TYPE_NUMBER, "Număr"),
    ]

    job = models.ForeignKey("jobs.Job", related_name="questions", on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_YESNO)
    required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"[{self.job_id}] {self.text}"


class SavedJob(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="saved_jobs", on_delete=models.CASCADE)
    job = models.ForeignKey("jobs.Job", related_name="saved_by", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "job")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} → {self.job_id}"


class JobReport(models.Model):
    REASON_SPAM = "spam"
    REASON_DUP = "duplicate"
    REASON_CONTACT = "contact_info"
    REASON_SCAM = "scam"
    REASON_OTHER = "other"
    REASONS = [
        (REASON_SPAM, "Spam"),
        (REASON_DUP, "Duplicate"),
        (REASON_CONTACT, "Date contact în anunț"),
        (REASON_SCAM, "Înșelătorie"),
        (REASON_OTHER, "Alt motiv"),
    ]
    job = models.ForeignKey(Job, related_name="reports", on_delete=models.CASCADE)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="job_reports")
    reason = models.CharField(max_length=32, choices=REASONS)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report {self.id} on {self.job_id}"

