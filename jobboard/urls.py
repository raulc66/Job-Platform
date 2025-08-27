from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from apps.jobs.sitemaps import JobSitemap

sitemaps = {"jobs": JobSitemap}

urlpatterns = [
    path("admin/", admin.site.urls),

    # Public apps
    path("", include(("apps.jobs.urls", "jobs"), namespace="jobs")),
    path("companies/", include(("apps.companies.urls", "companies"), namespace="companies")),
    path("applications/", include(("apps.applications.urls", "applications"), namespace="applications")),

    # Auth (allauth)
    path("accounts/", include("allauth.urls")),

    # Sitemap
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)