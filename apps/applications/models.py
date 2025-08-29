from django.conf import settings
from django.db import models
from apps.jobs.models import Job


class Application(models.Model):
    STATUS_CHOICES = [
        ("submitted", "Trimisă"),
        ("viewed", "Vizualizată"),
        ("interview", "Interviu"),
        ("offer", "Ofertă"),
        ("rejected", "Respinsă"),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications", verbose_name="Job")
    seeker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications", verbose_name="Candidat")
    cover_letter = models.TextField(blank=True, null=True, verbose_name="Scrisoare de intenție")
    cv = models.FileField(upload_to="cvs/%Y/%m/", blank=True, null=True, verbose_name="CV")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="submitted", verbose_name="Stare")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creat la")

    class Meta:
        unique_together = (("job", "seeker"),)
        ordering = ["-created_at"]
        verbose_name = "Aplicație"
        verbose_name_plural = "Aplicații"

    def __str__(self):
        return f"{self.seeker} → {self.job}"


class ApplicationAnswer(models.Model):
    application = models.ForeignKey("applications.Application", related_name="answers", on_delete=models.CASCADE)
    question = models.ForeignKey("jobs.JobQuestion", related_name="answers", on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("application", "question")
        ordering = ["id"]

    def __str__(self):
        return f"A{self.application_id}:Q{self.question_id}"