from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("jobs/", include("apps.jobs.urls")),
    path("applications/", include("apps.applications.urls")),
    path("companies/", include("apps.companies.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)