from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django_filters.views import FilterView
from apps.accounts.decorators import EmployerRequiredMixin, role_required
from apps.companies.models import Company
from .forms import JobForm
from .models import Job, SavedJob, JobReport
from .filters import JobFilter
from django.utils import timezone
from datetime import timedelta
from django.utils.decorators import method_decorator
from apps.accounts.decorators import rate_limit
import re
from django.core.mail import send_mail
from django.conf import settings
from apps.analytics.utils import log_event

PROFANITY_WORDS = {"fuck", "shit", "spam", "escroc", "teapa", "teapă"}

class JobListView(FilterView, ListView):
    model = Job
    paginate_by = 20
    template_name = "jobs/job_list.html"
    context_object_name = "jobs"
    filterset_class = JobFilter

    def get_queryset(self):
        return Job.objects.select_related("company").filter(is_active=True)

class JobDetailView(DetailView):
    model = Job
    template_name = "jobs/job_detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        try:
            log_event(request, "job_view", {"job_id": self.object.id, "slug": self.object.slug})
        except Exception:
            pass
        return response

@method_decorator(rate_limit(key="job-create", rate=5, period=60), name="dispatch")  # 5/min per user/IP
class JobCreateView(EmployerRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = "jobs/job_form.html"

    def dispatch(self, request, *args, **kwargs):
        # Require at least one company owned by the employer
        if not Company.objects.filter(owner=request.user).exists():
            messages.warning(request, "Trebuie să adaugi o companie înainte de a posta un job.")
            return redirect("companies:need_company")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user

        # Duplicate detection in last 7 days (same company + title + location/city if present)
        fields = {f.name for f in Job._meta.get_fields()}
        company = form.cleaned_data.get("company")
        title = (form.cleaned_data.get("title") or "").strip()
        location = (form.cleaned_data.get("location") or "").strip() if "location" in fields else ""
        city = (form.cleaned_data.get("city") or "").strip() if "city" in fields else ""
        since = timezone.now() - timedelta(days=7)

        dup_qs = Job.objects.filter(company=company, title__iexact=title, created_at__gte=since)
        if "location" in fields and location:
            dup_qs = dup_qs.filter(location__iexact=location)
        elif "city" in fields and city:
            dup_qs = dup_qs.filter(city__iexact=city)

        # Abuse detection: simple profanity + contact leakage already redacted in form, still flag if obvious
        desc = (form.cleaned_data.get("description") or "").lower()
        has_profanity = any(w in desc for w in PROFANITY_WORDS)
        has_contact_leak = bool(re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", desc, re.I)) or bool(re.search(r"\+?\d[\d\s().-]{6,}\d", desc))

        # Moderation rule: first 5 approved jobs by this employer require approval
        approved_count = Job.objects.filter(created_by=self.request.user, moderation_status=Job.MOD_APPROVED).count()
        requires_review = approved_count < 5

        flagged_reason = ""
        if dup_qs.exists():
            requires_review = True
            flagged_reason = "duplicate"
        elif has_profanity:
            requires_review = True
            flagged_reason = "abuse"
        elif has_contact_leak:
            requires_review = True
            flagged_reason = "contact_info"

        if requires_review:
            form.instance.moderation_status = Job.MOD_PENDING
            if "is_active" in fields:
                form.instance.is_active = False
            if flagged_reason:
                form.instance.flagged_reason = flagged_reason
                form.instance.flagged_at = timezone.now()
        else:
            form.instance.moderation_status = Job.MOD_APPROVED
            form.instance.approved_at = timezone.now()
            if "is_active" in fields:
                form.instance.is_active = True

        # Enforce ownership of company (already done above)
        company = form.cleaned_data.get("company")
        if company and getattr(company, "owner_id", None) != self.request.user.id:
            return HttpResponseForbidden("Nu ai permisiunea de a posta pentru această companie.")

        response = super().form_valid(form)
        try:
            log_event(self.request, "job_posted", {"job_id": self.object.id, "slug": self.object.slug})
        except Exception:
            pass
        return response

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        try:
            form.fields["company"].queryset = Company.objects.filter(owner=self.request.user)
        except Exception:
            pass
        return form

@login_required
@role_required("employer")
def job_create(request):
    # Employer must have at least one company
    if not Company.objects.filter(owner=request.user).exists():
        messages.warning(request, "Trebuie să adaugi o companie înainte de a posta un job.")
        return redirect("companies:need_company")

    if request.method == "POST":
        form = JobForm(request.POST, request.FILES)
        # Limit selectable companies to those owned by this employer
        form.fields["company"].queryset = Company.objects.filter(owner=request.user)
        if form.is_valid():
            job = form.save(commit=False)
            # Safety: enforce company ownership
            if job.company.owner_id != request.user.id:
                return HttpResponseForbidden("Nu ai permisiunea de a posta pentru această companie.")
            job.save()
            messages.success(request, "Jobul a fost creat.")
            return redirect("jobs:detail", slug=job.slug)
    else:
        form = JobForm()
        form.fields["company"].queryset = Company.objects.filter(owner=request.user)

    return render(request, "jobs/job_form.html", {"form": form})

@login_required
@role_required("employer")
def job_update(request, slug):
    job = get_object_or_404(Job, slug=slug)
    # Only the employer owning the job's company can edit
    if job.company.owner_id != request.user.id:
        return HttpResponseForbidden("Nu ai permisiunea de a edita acest job.")

    if request.method == "POST":
        form = JobForm(request.POST, request.FILES, instance=job)
        form.fields["company"].queryset = Company.objects.filter(owner=request.user)
        if form.is_valid():
            job = form.save(commit=False)
            if job.company.owner_id != request.user.id:
                return HttpResponseForbidden("Nu ai permisiunea de a edita pentru această companie.")
            job.save()
            messages.success(request, "Jobul a fost actualizat.")
            return redirect("jobs:detail", slug=job.slug)
    else:
        form = JobForm(instance=job)
        form.fields["company"].queryset = Company.objects.filter(owner=request.user)

    return render(request, "jobs/job_form.html", {"form": form, "job": job})

def job_list(request):
    qs = Job.objects.select_related("company")
    # Hide inactive jobs if the field exists
    field_names = {f.name for f in Job._meta.get_fields()}
    if "is_active" in field_names:
        qs = qs.filter(is_active=True)

    # Filtering
    job_filter = JobFilter(request.GET or None, queryset=qs)
    qs = job_filter.qs

    # Sorting
    sort = request.GET.get("sort", "newest")
    if sort == "salary_desc" and "salary_max" in field_names:
        qs = qs.order_by("-salary_max", "-created_at") if "created_at" in field_names else qs.order_by("-salary_max")
    else:
        qs = qs.order_by("-created_at") if "created_at" in field_names else qs

    # Pagination
    paginator = Paginator(qs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Preserve query (without page) for pagination links
    qcopy = request.GET.copy()
    qcopy.pop("page", None)
    preserved_query = qcopy.urlencode()

    context = {
        "filter": job_filter,
        "page_obj": page_obj,
        "preserved_query": preserved_query,
        "sort": sort,
    }
    return render(request, "jobs/job_list.html", context)

def job_detail(request, slug):
    qs = Job.objects.select_related("company")
    field_names = {f.name for f in Job._meta.get_fields()}
    if "is_active" in field_names:
        job = get_object_or_404(qs, slug=slug, is_active=True)
    else:
        job = get_object_or_404(qs, slug=slug)
    return render(request, "jobs/job_detail.html", {"job": job})

@login_required
@role_required("seeker")
def save_job(request, slug):
    job = get_object_or_404(Job, slug=slug)
    SavedJob.objects.get_or_create(user=request.user, job=job)
    messages.success(request, "Job salvat.")
    return redirect("jobs:detail", slug=slug)

@login_required
@role_required("seeker")
def unsave_job(request, slug):
    job = get_object_or_404(Job, slug=slug)
    SavedJob.objects.filter(user=request.user, job=job).delete()
    messages.info(request, "Job eliminat din favorite.")
    return redirect("jobs:detail", slug=slug)

@login_required
def report_job(request, slug):
    job = get_object_or_404(Job, slug=slug)
    if request.method == "POST":
        reason = request.POST.get("reason", "other")
        notes = request.POST.get("notes", "").strip()
        JobReport.objects.create(job=job, reporter=request.user, reason=reason, notes=notes)

        # Notify staff/admins (console backend in dev)
        recipients = [email for _, email in getattr(settings, "ADMINS", [])] or [getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@localhost")]
        subject = f"[Report job] {job.title}"
        body = f"Job: {job.title}\nCompanie: {getattr(job.company, 'name', '')}\nReporter: {request.user.username}\nMotiv: {reason}\nDetalii: {notes}\nURL: {request.build_absolute_uri(job.get_absolute_url())}"
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True)
        except Exception:
            pass

        messages.success(request, "Mulțumim pentru raportare. Echipa va verifica anunțul.")
        return redirect("jobs:detail", slug=slug)
    return redirect("jobs:detail", slug=slug)