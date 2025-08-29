from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from apps.accounts.decorators import rate_limit, role_required
from apps.accounts.utils import is_disposable_email
from django.utils import timezone
from datetime import timedelta
from apps.jobs.models import Job, SavedJob
from .models import Application, ApplicationAnswer
from .forms import ApplicationForm  # use the correct form
from apps.analytics.utils import log_event


@login_required
@role_required("seeker")
@rate_limit(key="apply", rate=10, period=60)  # 10/min per user/IP
def apply(request, slug):
    job = get_object_or_404(Job.objects.select_related("company"), slug=slug)
    if request.method == "GET":
        try:
            log_event(request, "apply_started", {"job_id": job.id, "slug": job.slug})
        except Exception:
            pass
    existing = Application.objects.filter(job=job, seeker=request.user).first()
    if existing:
        messages.info(request, "Ai aplicat deja la acest job.")
        return redirect("jobs:detail", slug=job.slug)

    questions = list(getattr(job, "questions", Job.objects.none()).all())

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        # Build answers dict from POST
        answers_payload = {}
        for q in questions:
            key = f"q_{q.id}"
            val = request.POST.get(key, "").strip()
            if q.type == "yes_no":
                # checkbox returns "on" or missing; accept "true/false" too
                val = "da" if request.POST.get(key) in ("on", "true", "1", "da") else "nu"
            if q.required and not val:
                form.add_error(None, f"Răspunsul la întrebarea „{q.text}” este obligatoriu.")
            answers_payload[q.id] = val

        if form.is_valid():
            app = form.save(commit=False)
            app.job = job
            app.seeker = request.user
            # If Application has 'status', default to 'submitted'
            if hasattr(app, "status") and not app.status:
                app.status = getattr(Application, "STATUS_SUBMITTED", "submitted")
            app.save()

            for q in questions:
                ApplicationAnswer.objects.create(application=app, question=q, answer_text=answers_payload.get(q.id, ""))

            # Notificare email (console în dev)
            job_url = request.build_absolute_uri(reverse("jobs:detail", kwargs={"slug": job.slug}))
            subject = f"[Aplicație nouă] {job.title}"
            seeker_name = request.user.get_full_name() or request.user.username
            seeker_email = getattr(request.user, "email", "")
            message_lines = [
                f"A fost trimisă o aplicație nouă pentru jobul: {job.title}",
                f"Companie: {getattr(job.company, 'name', '')}",
                f"Candidat: {seeker_name} ({seeker_email})",
                f"Vezi jobul: {job_url}",
            ]
            message = "\n".join([l for l in message_lines if l])

            # Destinatari: proprietarul companiei dacă are email; altfel ADMINS
            recipients = []
            company_owner = getattr(job, "company", None) and getattr(job.company, "owner", None)
            owner_email = getattr(company_owner, "email", None)
            if owner_email:
                recipients.append(owner_email)
            else:
                recipients.extend([email for _, email in getattr(settings, "ADMINS", [])])

            if recipients:
                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True)
                except Exception:
                    # în dev ignorăm erorile email
                    pass

            try:
                log_event(request, "apply_submitted", {"job_id": job.id, "application_id": app.id})
            except Exception:
                pass

            messages.success(request, "Aplicația a fost trimisă.")
            return redirect("jobs:detail", slug=job.slug)
    else:
        form = ApplicationForm()

    # Block disposable email domains
    if is_disposable_email(getattr(request.user, "email", "")):
        messages.error(request, "Adresa de email pare a fi temporară. Te rugăm folosește o adresă validă.")
        return redirect("jobs:detail", slug=slug)

    return render(request, "applications/apply.html", {"job": job, "form": form, "questions": questions})


@login_required
@role_required("seeker")
def my_applications(request):
    apps_qs = Application.objects.filter(seeker=request.user).select_related("job", "job__company").order_by("-id")
    saved = SavedJob.objects.filter(user=request.user).select_related("job", "job__company")
    return render(request, "applications/my_applications.html", {"applications": apps_qs, "saved_jobs": saved})