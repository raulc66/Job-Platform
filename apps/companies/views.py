from django.db.models import Prefetch
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import EmployerRequiredMixin, role_required
from apps.jobs.models import Job
from apps.applications.models import Application
from apps.applications.models import ApplicationAnswer
from .models import Company
from apps.analytics.utils import log_event


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
    # Employer must own at least one company
    companies = Company.objects.filter(owner=request.user)
    jobs = Job.objects.filter(company__in=companies)
    apps_qs = (
        Application.objects.filter(job__in=jobs)
        .select_related("job", "job__company", "seeker")
        .prefetch_related(Prefetch("answers", queryset=ApplicationAnswer.objects.select_related("question")))
        .order_by("-id")
    )

    # Handle status update (if Application has status field)
    if request.method == "POST":
        app_id = request.POST.get("app_id")
        new_status = request.POST.get("status")
        app = apps_qs.filter(id=app_id).first()
        if app and hasattr(app, "status") and new_status:
            app.status = new_status
            app.save(update_fields=["status"])
            try:
                log_event(request, "status_changed", {"application_id": app.id, "status": new_status})
            except Exception:
                pass
            messages.success(request, "Status actualizat.")
            return redirect("companies:employer_applicants")

    return render(request, "companies/employer_applicants.html", {"applications": apps_qs})