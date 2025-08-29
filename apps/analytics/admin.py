from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "path", "request_id", "created_at")
    list_filter = ("name", "created_at")
    search_fields = ("name", "path", "request_id", "user__username")
