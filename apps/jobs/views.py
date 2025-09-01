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
from django.db.models import Q

PROFANITY_WORDS = {"fuck", "shit", "spam", "escroc", "teapa", "teapă"}

class JobListView(FilterView, ListView):
    model = Job
    paginate_by = 20
    template_name = "jobs/job_list.html"
    context_object_name = "jobs"
    filterset_class = JobFilter

    def get_queryset(self):
        qs = super().get_queryset().select_related("company")
        params = self.request.GET

        # Field presence checks
        fields = {f.name for f in Job._meta.get_fields()}
        has_is_active = "is_active" in fields
        has_moderation = "moderation_status" in fields
        has_location = "location" in fields
        has_city = "city" in fields
        has_employment_type = "employment_type" in fields
        has_work_type = "work_type" in fields
        has_salary_min = "salary_min" in fields
        has_salary_max = "salary_max" in fields

        # Only public jobs
        if has_is_active:
            qs = qs.filter(is_active=True)
        if has_moderation:
            qs = qs.filter(moderation_status=getattr(Job, "MOD_APPROVED", "approved"))

        # Search
        q = (params.get("q") or "").strip()
        if q:
            q_filter = Q(title__icontains=q) | Q(description__icontains=q)
            if "company" in fields:
                q_filter = q_filter | Q(company__name__icontains=q)
            qs = qs.filter(q_filter)

        # Location
        loc = (params.get("loc") or "").strip()
        if loc:
            if has_location:
                qs = qs.filter(location__icontains=loc)
            elif has_city:
                qs = qs.filter(city__icontains=loc)

        # Employment type
        emp = (params.get("employment_type") or "").strip()
        if emp and has_employment_type:
            qs = qs.filter(employment_type=emp)

        # Work type (e.g., remote/hybrid/onsite)
        work = (params.get("work_type") or "").strip()
        if work and has_work_type:
            qs = qs.filter(work_type=work)

        # Has salary
        has_salary = params.get("has_salary")
        if has_salary in ("1", "true", "on", "yes"):
            if has_salary_max:
                qs = qs.filter(salary_max__isnull=False)
            elif has_salary_min:
                qs = qs.filter(salary_min__isnull=False)

        # Sorting
        sort = (params.get("sort") or "new").strip()
        if sort == "salary":
            if has_salary_max:
                qs = qs.order_by("-salary_max", "-id")
            elif has_salary_min:
                qs = qs.order_by("-salary_min", "-id")
            else:
                qs = qs.order_by("-id")
        else:
            qs = qs.order_by("-created_at" if "created_at" in fields else "-id")

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()

        # Build querystring without page for pagination persistence
        params_without_page = params.copy()
        params_without_page.pop("page", None)
        querystring = params_without_page.urlencode()

        # Active filters for chips
        active_filters = {}
        if params.get("q"): active_filters["q"] = params.get("q")
        if params.get("loc"): active_filters["loc"] = params.get("loc")
        if params.get("employment_type"): active_filters["employment_type"] = params.get("employment_type")
        if params.get("work_type"): active_filters["work_type"] = params.get("work_type")
        if params.get("has_salary") in ("1", "true", "on", "yes"): active_filters["has_salary"] = "1"
        if params.get("sort") and params.get("sort") != "new": active_filters["sort"] = params.get("sort")

        # Remove-links (URL for current list without that param)
        remove_links = {}
        for key in active_filters.keys():
            p = params.copy()
            p.pop(key, None)
            p.pop("page", None)
            remove_links[key] = f"?{p.urlencode()}" if p else "?"

        # Choices for selects (if fields exist with choices)
        def field_choices(name):
            try:
                f = Job._meta.get_field(name)
                return list(f.choices) if getattr(f, "choices", None) else []
            except Exception:
                return []

        ctx.update({
            "query": params,
            "querystring": querystring,
            "active_filters": active_filters,
            "remove_links": remove_links,
            "employment_type_choices": field_choices("employment_type"),
            "work_type_choices": field_choices("work_type"),
        })

        profile = None
        quick_apply_ready = False
        if self.request.user.is_authenticated:
            try:
                quick_apply_ready = bool(getattr(self.request.user, "seekerprofile", None) and self.request.user.seekerprofile.quick_apply_ready)
            except Exception:
                quick_apply_ready = False
        ctx["quick_apply_ready"] = quick_apply_ready
        return ctx

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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        job = self.object
        fields = {f.name for f in Job._meta.get_fields()}

        qs = Job.objects.exclude(id=job.id).select_related("company")
        if "is_active" in fields:
            qs = qs.filter(is_active=True)
        if "moderation_status" in fields:
            qs = qs.filter(moderation_status=getattr(Job, "MOD_APPROVED", "approved"))

        filters = Q()
        # Heuristic matching by category/city/location/work_type
        if "category" in fields and getattr(job, "category_id", None):
            filters |= Q(category_id=job.category_id)
        if "city" in fields and getattr(job, "city", ""):
            filters |= Q(city__iexact=job.city)
        elif "location" in fields and getattr(job, "location", ""):
            filters |= Q(location__iexact=job.location)
        if "work_type" in fields and getattr(job, "work_type", ""):
            filters |= Q(work_type=job.work_type)

        if filters:
            qs = qs.filter(filters)

        order_field = "-created_at" if "created_at" in fields else "-id"
        similar_jobs = list(qs.order_by(order_field)[:4])
        ctx["similar_jobs"] = similar_jobs
        return ctx

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