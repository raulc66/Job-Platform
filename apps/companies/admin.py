from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "is_verified", "created_at")
    search_fields = ("name",)
    list_filter = ("is_verified",)
    readonly_fields = ("created_at",)

    @admin.action(description="Verify selected companies")
    def verify_companies(self, request, queryset):
        queryset.update(is_verified=True)

    actions = ("verify_companies",)