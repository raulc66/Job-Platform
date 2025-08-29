from django.urls import path
from . import views

app_name = "companies"

urlpatterns = [
    path("", views.company_list, name="list"),
    path("dashboard/", views.EmployerDashboardView.as_view(), name="dashboard"),
    path("need-company/", views.need_company, name="need_company"),
    path("applicants/", views.employer_applicants, name="employer_applicants"),
    path("<slug:slug>/", views.company_detail, name="detail"),
]