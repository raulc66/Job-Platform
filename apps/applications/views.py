from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
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