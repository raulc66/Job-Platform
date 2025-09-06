from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from apps.jobs.models import SavedJob

User = get_user_model()

@shared_task
def send_saved_jobs_digest(frequency="daily"):
    # Very basic digest: all users who have saved jobs get a summary
    users = (
        User.objects.filter(saved_jobs__isnull=False)
        .distinct()
        .prefetch_related("saved_jobs__job", "saved_jobs__job__company")
    )
    for user in users:
        saved = list(SavedJob.objects.filter(user=user).select_related("job", "job__company")[:20])
        if not saved:
            continue
        ctx = {"user": user, "saved": saved, "frequency": frequency}
        body = render_to_string("emails/saved_jobs_digest.txt", ctx)
        try:
            send_mail(
                subject=f"[Rezumat joburi salvate] {frequency}",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email] if user.email else [],
                fail_silently=True,
            )
        except Exception:
            pass

def notify_saved_jobs():
    qs = User.objects.filter(saved_jobs__isnull=False).distinct()
