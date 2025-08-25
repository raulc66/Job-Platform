from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView
from django_filters.views import FilterView
from .models import Job
from .forms import JobForm
from .filters import JobFilter
from apps.accounts.decorators import EmployerRequiredMixin

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
            from apps.companies.models import Company
            form.fields["company"].queryset = Company.objects.filter(owner=self.request.user)
        except Exception:
            pass
        return form