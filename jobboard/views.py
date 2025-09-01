from urllib.parse import urlencode
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone

from apps.jobs.models import Job
from apps.companies.models import Company
from apps.applications.models import Application

def home(request):
    # Redirect search to /jobs/?q=...&loc=...
    q = (request.GET.get("q") or "").strip()
    loc = (request.GET.get("loc") or "").strip()
    if request.method == "GET" and (q or loc) and (set(request.GET.keys()) & {"q", "loc"}):
        url = reverse("jobs:list")
        params = {}
        if q:
            params["q"] = q
        if loc:
            params["loc"] = loc
        return redirect(f"{url}?{urlencode(params)}")

    # Counts
    now = timezone.now()
    start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    job_fields = {f.name for f in Job._meta.get_fields()}
    jobs_qs = Job.objects.all()
    if "is_active" in job_fields:
        jobs_qs = jobs_qs.filter(is_active=True)
    if "moderation_status" in job_fields:
        jobs_qs = jobs_qs.filter(moderation_status=getattr(Job, "MOD_APPROVED", "approved"))

    jobs_active_count = jobs_qs.count()
    companies_count = Company.objects.count()

    app_fields = {f.name for f in Application._meta.get_fields()}
    apps_qs = Application.objects.all()
    if "created_at" in app_fields:
        apps_qs = apps_qs.filter(created_at__gte=start_month)
    applications_month_count = apps_qs.count()

    ctx = {
        "jobs_active_count": jobs_active_count,
        "companies_count": companies_count,
        "applications_month_count": applications_month_count,
        "q": q,
        "loc": loc,
    }
    return render(request, "home.html", ctx)
