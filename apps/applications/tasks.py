from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from apps.applications.models import Application

@shared_task
def send_application_notification(app_id: int):
    app = Application.objects.select_related("job", "job__company", "seeker").filter(id=app_id).first()
    if not app:
        return
    job = app.job
    job_url = f"{settings.SITE_URL.rstrip('/')}{reverse('jobs:detail', kwargs={'slug': job.slug})}" if getattr(settings, "SITE_URL", "") else reverse("jobs:detail", kwargs={"slug": job.slug})
    subject = f"[Aplicație nouă] {job.title}"
    seeker_name = app.seeker.get_full_name() or app.seeker.username
    seeker_email = getattr(app.seeker, "email", "")
    message_lines = [
        f"A fost trimisă o aplicație nouă pentru jobul: {job.title}",
        f"Companie: {getattr(job.company, 'name', '')}",
        f"Candidat: {seeker_name} ({seeker_email})",
        f"Vezi jobul: {job_url}",
    ]
    recipients = [email for _, email in getattr(settings, "ADMINS", [])]
    if not recipients:
        recipients = [getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@localhost")]
    try:
        send_mail(subject, "\n".join(message_lines), settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True)
    except Exception:
        pass
