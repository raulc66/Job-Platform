from django.contrib.sitemaps import Sitemap
from .models import Job


class JobSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Job.objects.filter(is_active=True)

    def lastmod(self, obj: Job):
        return obj.updated_at