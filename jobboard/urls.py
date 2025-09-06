from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("jobs/", include("apps.jobs.urls")),
    path("applications/", include("apps.applications.urls")),
    path("companies/", include("apps.companies.urls")),
    path("accounts/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    path("admin/", admin.site.urls),

    # Back-compat names used by tests
    path("accounts/login/", RedirectView.as_view(pattern_name="accounts:login", permanent=False), name="account_login"),
    path("accounts/register/", RedirectView.as_view(pattern_name="accounts:register", permanent=False), name="account_signup"),
    path("accounts/logout/", RedirectView.as_view(pattern_name="accounts:logout", permanent=False), name="account_logout"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)