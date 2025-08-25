from django.urls import path
from .views import EmployerDashboardView, company_list, company_detail

app_name = "companies"

urlpatterns = [
    path("dashboard/", EmployerDashboardView.as_view(), name="dashboard"),
    path("", company_list, name="list"),
    path("<int:pk>/", company_detail, name="detail"),
]