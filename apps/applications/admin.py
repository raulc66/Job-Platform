from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "seeker", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("job__title", "seeker__email", "seeker__first_name", "seeker__last_name")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    autocomplete_fields = ("job", "seeker")

    # Ensure no invalid fields are declared anywhere
    # fields, fieldsets, or add_fieldsets should only use the real model fields:
    # job, seeker, cover_letter, cv, status, created_at