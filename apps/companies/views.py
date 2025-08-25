from django.db.models import Prefetch
from django.shortcuts import render
from django.views.generic import TemplateView
from apps.accounts.decorators import EmployerRequiredMixin
from apps.jobs.models import Job
from apps.applications.models import Application


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
from .models import Company

def company_list(request):
    companies = Company.objects.all()
    return render(request, 'companies/company_list.html', {'companies': companies})

def company_detail(request, pk):
    company = Company.objects.get(pk=pk)
    return render(request, 'companies/company_detail.html', {'company': company})