from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from apps.accounts.decorators import role_required
from apps.jobs.models import Job
from .models import Application
from .forms import ApplicationForm  # use the correct form


@login_required
@role_required("seeker")
def apply(request, slug):
    job = get_object_or_404(Job, slug=slug)
    existing = Application.objects.filter(job=job, seeker=request.user).first()
    if existing:
        messages.info(request, "Ai aplicat deja la acest job.")
        return redirect("jobs:detail", slug=job.slug)

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.job = job
            app.seeker = request.user
            app.save()

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

            messages.success(request, "Aplicația a fost trimisă.")
            return redirect("jobs:detail", slug=job.slug)
    else:
        form = ApplicationForm()

    return render(request, "applications/apply.html", {"job": job, "form": form})


@login_required
@role_required("seeker")
def my_applications(request):
    qs = Application.objects.filter(seeker=request.user).select_related("job", "job__company")
    return render(request, "applications/my_applications.html", {"applications": qs})