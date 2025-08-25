import django_filters as filters
from .models import Job


class JobFilter(filters.FilterSet):
    q = filters.CharFilter(method="search", label="Search")

    class Meta:
        model = Job
        fields = ["category", "city", "is_active"]

    def search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(title__icontains=value) | queryset.filter(description__icontains=value)