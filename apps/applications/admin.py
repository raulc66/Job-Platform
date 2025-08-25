from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "applicant", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "email", "job__title")
    readonly_fields = ("created_at",)