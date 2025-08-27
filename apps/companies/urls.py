from django.urls import path
from . import views

app_name = "companies"

urlpatterns = [
    path("", views.company_list, name="list"),
    path("<slug:slug>/", views.company_detail, name="detail"),
    path("employer/need-company/", views.need_company, name="need_company"),
    path("employer/applicants/", views.employer_applicants, name="employer_applicants"),
]