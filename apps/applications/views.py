from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import FormView
from apps.jobs.models import Job
from .models import Application
from apps.accounts.decorators import SeekerRequiredMixin


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["full_name", "email", "phone", "cv", "cover_letter"]

    def __init__(self, *args, **kwargs):
        self.job = kwargs.pop("job", None)
        self.applicant = kwargs.pop("applicant", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.job = self.job
        obj.applicant = self.applicant
        if commit:
            obj.save()
        return obj


class ApplyView(SeekerRequiredMixin, FormView):
    form_class = ApplicationForm
    template_name = "applications/application_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.job = get_object_or_404(Job, slug=kwargs["slug"], is_active=True)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["job"] = self.job
        kwargs["applicant"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy("jobs:detail", kwargs={"slug": self.job.slug})