from django.urls import path
from .views import JobListView, JobDetailView, JobCreateView


app_name = "jobs"

urlpatterns = [
    path("", JobListView.as_view(), name="list"),
    path("new/", JobCreateView.as_view(), name="create"),
    path("<slug:slug>/", JobDetailView.as_view(), name="detail"),
]