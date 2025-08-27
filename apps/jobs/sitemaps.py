from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Job


class JobSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7

    def items(self):
        qs = Job.objects.select_related("company")
        if "is_active" in {f.name for f in Job._meta.get_fields()}:
            qs = qs.filter(is_active=True)
        return qs

    def lastmod(self, obj):
        return getattr(obj, "updated_at", getattr(obj, "created_at", None))

    def location(self, obj):
        try:
            return obj.get_absolute_url()
        except Exception:
            return reverse("jobs:detail", kwargs={"slug": obj.slug})