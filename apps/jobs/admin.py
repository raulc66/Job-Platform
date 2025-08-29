from django.contrib import admin
from .models import Job, JobReport


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "moderation_status", "flagged_reason", "created_by", "created_at")
    list_filter = ("moderation_status", "flagged_reason", "company")
    search_fields = ("title", "company__name", "description", "slug")
    actions = ["approve_jobs", "reject_jobs"]

    def approve_jobs(self, request, queryset):
        updated = 0
        for job in queryset:
            job.approve()
            updated += 1
        self.message_user(request, f"{updated} job(uri) aprobate.")
    approve_jobs.short_description = "Aprobă joburile selectate"

    def reject_jobs(self, request, queryset):
        for job in queryset:
            job.reject(reason="admin")
        self.message_user(request, "Joburile selectate au fost respinse.")
    reject_jobs.short_description = "Respinge joburile selectate"


@admin.register(JobReport)
class JobReportAdmin(admin.ModelAdmin):
    list_display = ("job", "reason", "reporter", "handled", "created_at")
    list_filter = ("reason", "handled")
    search_fields = ("job__title", "reporter__username", "notes")

# Register other models if not already:
# admin.site.register(JobQuestion)
# admin.site.register(SavedJob)