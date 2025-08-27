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
from .models import Job
from .filters import JobFilter

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
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "jobs/job_detail.html"
    context_object_name = "job"

class JobCreateView(EmployerRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = "jobs/job_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

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