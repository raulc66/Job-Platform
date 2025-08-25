from django import forms
from .models import Job


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ["company", "title", "category", "city", "description", "salary_min", "salary_max", "is_active", "expires_at"]