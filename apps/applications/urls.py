from django.urls import path
from . import views

app_name = "applications"

urlpatterns = [
    # User-facing
    path("apply/<slug:slug>/", views.apply, name="apply"),
    path("mine/", views.my_applications, name="mine"),

    # Employer-facing inbox
    path("employer/inbox/", views.inbox, name="inbox"),
    path("employer/inbox/export.csv", views.export_csv, name="export_csv"),

    # Status updates
    path("status/", views.update_status, name="status_update_base"),           # JSON body {id,status}
    path("status/<int:pk>/", views.update_status, name="status_update"),      # Preferred
]