from django.db.models import Prefetch
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import EmployerRequiredMixin, role_required
from apps.jobs.models import Job
from apps.applications.models import Application
from .models import Company


class EmployerDashboardView(EmployerRequiredMixin, TemplateView):
    template_name = "companies/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        jobs = (
            Job.objects.filter(company__owner=self.request.user)
            .prefetch_related(
                Prefetch("applications", queryset=Application.objects.select_related("applicant", "job"))
            )
        )
        ctx["jobs"] = jobs
        return ctx


def company_list(request):
    companies = Company.objects.all().order_by("name")
    return render(request, "companies/company_list.html", {"companies": companies})


def company_detail(request, slug):
    company = get_object_or_404(Company, slug=slug)
    jobs = Job.objects.filter(company=company).select_related("company")
    # If Job has is_active, filter active ones
    if hasattr(Job, "is_active"):
        jobs = jobs.filter(is_active=True)
    return render(request, "companies/company_detail.html", {"company": company, "jobs": jobs})


@login_required
@role_required("employer")
def need_company(request):
    # Simple info page guiding employers to add a company
    return render(request, "companies/need_company.html")


@login_required
@role_required("employer")
def employer_applicants(request):
    # Applications for jobs owned by the employer's companies
    company_ids = Company.objects.filter(owner=request.user).values_list("id", flat=True)
    apps_qs = (
        Application.objects
        .filter(job__company_id__in=list(company_ids))
        .select_related("job", "job__company", "seeker")
        .order_by("-created_at")
    )
    return render(request, "companies/employer_applicants.html", {"applications": apps_qs})