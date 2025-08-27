from django.contrib import admin
from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title", "company__name", "location")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at",)

    @admin.action(description="Închide joburile selectate")
    def close_jobs(self, request, queryset):
        queryset.update(is_active=False)

    actions = ("close_jobs",)