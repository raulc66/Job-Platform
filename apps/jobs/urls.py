from django.urls import path
from .views import JobListView, JobDetailView, JobCreateView, job_update, save_job, unsave_job, report_job


app_name = "jobs"

urlpatterns = [
    path("", JobListView.as_view(), name="list"),
    path("new/", JobCreateView.as_view(), name="create"),
    path("<slug:slug>/save/", save_job, name="save"),
    path("<slug:slug>/unsave/", unsave_job, name="unsave"),
    path("<slug:slug>/report/", report_job, name="report"),
    path("<slug:slug>/edit/", job_update, name="edit"),
    path("<slug:slug>/", JobDetailView.as_view(), name="detail"),
]