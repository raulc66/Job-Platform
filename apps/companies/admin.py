from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "owner__email", "owner__username")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at",)