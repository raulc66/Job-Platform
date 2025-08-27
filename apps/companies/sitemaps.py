from django.contrib.sitemaps import Sitemap
from .models import Company

class CompanySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return Company.objects.all()

    def lastmod(self, obj):
        return getattr(obj, "updated_at", getattr(obj, "created_at", None))

    def location(self, obj):
        if hasattr(obj, "get_absolute_url"):
            return obj.get_absolute_url()
        return f"/companies/{obj.slug}/"
