from django.contrib import admin
from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "category", "city", "is_active", "created_at")
    list_filter = ("category", "city", "is_active")
    search_fields = ("title", "company__name")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")

    @admin.action(description="Close selected jobs")
    def close_jobs(self, request, queryset):
        queryset.update(is_active=False)

    actions = ("close_jobs",)