from django.urls import path
from . import views

app_name = "applications"

urlpatterns = [
    path("apply/<slug:slug>/", views.apply, name="apply"),
    path("mine/", views.my_applications, name="mine"),
]