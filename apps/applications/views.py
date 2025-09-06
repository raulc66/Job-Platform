from __future__ import annotations

import csv
import json
from typing import Dict, List, Tuple

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import QuerySet
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.decorators import employer_required
from apps.applications.forms import ApplicationForm
from .models import Application
from apps.jobs.models import Job


def _get_status_choices() -> Tuple[List[Tuple[str, str]], Dict[str, str]]:
    """
    Returns (choices, map) for Application.status. Falls back to default labels.
    """
    default = [
        ("submitted", "Neridicate"),
        ("viewed", "Văzute"),
        ("interview", "Interviu"),
        ("offer", "Ofertă"),
        ("rejected", "Respins"),
    ]
    try:
        field = Application._meta.get_field("status")
        if getattr(field, "choices", None):
            choices = [(str(k), str(v)) for k, v in field.choices]
        else:
            choices = default
    except Exception:
        choices = default
    return choices, {k: v for k, v in choices}


def _employer_company_or_redirect(request):
    """
    Return employer's company or redirect to setup page if missing.
    """
    prof = getattr(request.user, "employerprofile", None)
    company = getattr(prof, "company", None)
    if not company:
        messages.info(request, "Asociază o companie înainte de a vedea aplicațiile.")
        return redirect("companies:employer_setup")
    return company


@login_required
@employer_required
@require_GET
def inbox(request):
    """
    Employer-facing inbox with status/job filters and pagination.
    """
    company = _employer_company_or_redirect(request)
    if not hasattr(company, "id"):  # redirected
        return company

    choices, label_map = _get_status_choices()
    allowed_status = set(k for k, _ in choices)

    qs: QuerySet[Application] = (
        Application.objects.filter(job__company=company)
        .select_related("job", "job__company", "seeker")  # was "user"
        .order_by("-id")
    )

    status = request.GET.get("status") or ""
    if status and status in allowed_status:
        qs = qs.filter(status=status)

    job_id = request.GET.get("job") or ""
    if job_id:
        try:
            qs = qs.filter(job_id=int(job_id))
        except ValueError:
            pass

    paginator = Paginator(qs, 25)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)

    # Jobs list for filter
    jobs_qs = Job.objects.filter(company=company).only("id", "title").order_by("title")

    ctx = {
        "applications": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "jobs": jobs_qs,
        "status_choices": choices,
        "status_label_map": label_map,
        # Used by JS fallback; row carries its own data-url
        "status_update_url": reverse("applications:status_update_base"),
    }
    return render(request, "applications/inbox.html", ctx)


@login_required
@employer_required
@require_POST
def update_status(request, pk: int | str = None):
    """
    Update an application status. Path style: /applications/status/<pk>/ (preferred),
    or POST body JSON {id, status} (fallback when pk is None).
    """
    _, label_map = _get_status_choices()
    allowed_status = set(label_map.keys())

    try:
        payload = json.loads(request.body or "{}")
    except Exception:
        payload = {}

    if pk is None:
        pk = payload.get("id")

    if not pk:
        return JsonResponse({"ok": False, "error": "missing_id"}, status=400)

    app = get_object_or_404(Application.objects.select_related("job", "job__company"), pk=pk)

    # Ownership check: must belong to current employer's company
    company = _employer_company_or_redirect(request)
    if not hasattr(company, "id"):  # redirected, but for JSON respond 403
        return JsonResponse({"ok": False, "error": "no_company"}, status=403)

    if app.job.company_id != company.id:
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    new_status = payload.get("status") or request.POST.get("status")
    if not new_status or new_status not in allowed_status:
        return JsonResponse({"ok": False, "error": "invalid_status"}, status=400)

    app.status = new_status
    if hasattr(app, "status_changed_at"):
        try:
            app.status_changed_at = timezone.now()
        except Exception:
            pass
    app.save(update_fields=["status"] + (["status_changed_at"] if hasattr(app, "status_changed_at") else []))

    return JsonResponse({"ok": True, "status": new_status, "status_label": label_map.get(new_status, new_status)})


@login_required
@employer_required
@require_GET
def export_csv(request):
    """
    CSV export of filtered applications. Uses the same filters as the inbox.
    """
    company = _employer_company_or_redirect(request)
    if not hasattr(company, "id"):
        # redirect response from helper; turn into 302 to setup page
        return company

    choices, label_map = _get_status_choices()

    qs: QuerySet[Application] = (
        Application.objects.filter(job__company=company)
        .select_related("job", "job__company", "seeker")  # was "user"
        .order_by("-id")
    )

    status = request.GET.get("status") or ""
    if status and status in label_map:
        qs = qs.filter(status=status)

    job_id = request.GET.get("job") or ""
    if job_id:
        try:
            qs = qs.filter(job_id=int(job_id))
        except ValueError:
            pass

    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="applications.csv"'
    writer = csv.writer(resp)
    writer.writerow(["Job", "Candidat", "Email", "Trimis", "Status"])
    for a in qs.iterator():
        user = getattr(a, "user", None)
        username = getattr(user, "username", "") if user else ""
        email = getattr(user, "email", "") if user else ""
        job_title = a.job.title if getattr(a, "job", None) else ""
        created = getattr(a, "created_at", None)
        created_s = timezone.localtime(created).strftime("%Y-%m-%d %H:%M") if created else ""
        status_label = label_map.get(getattr(a, "status", ""), getattr(a, "status", ""))
        writer.writerow([job_title, username, email, created_s, status_label])
    return resp


@login_required
def apply(request, slug):
    # Require authenticated user; optionally restrict to seekers if your User model has a role flag.
    job = get_object_or_404(Job, slug=slug)
    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.seeker = request.user          # was: app.user = request.user
            app.job = job
            app.save()
            messages.success(request, "Aplicarea a fost trimisă.")
            return redirect("jobs:detail", slug=job.slug)
    else:
        form = ApplicationForm()
    return render(request, "applications/apply.html", {"form": form, "job": job})


@login_required
def my_applications(request):
    qs = (
        Application.objects
        .filter(seeker=request.user)                   # was: user=request.user
        .select_related("job", "job__company", "seeker")  # was: ...,"user"
        .order_by("-created_at")
    )
    return render(request, "applications/my_list.html", {"applications": qs})