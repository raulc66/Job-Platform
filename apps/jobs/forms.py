import re
from django import forms
from .models import Job

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{6,}\d)")


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = "__all__"
        help_texts = {
            "description": "Evitați publicarea de emailuri sau numere de telefon. Comunicarea se va face prin platformă.",
        }

    def clean(self):
        cleaned = super().clean()
        salary_min = cleaned.get("salary_min")
        salary_max = cleaned.get("salary_max")
        if salary_min is not None and salary_max is not None:
            try:
                if salary_min > salary_max:
                    self.add_error("salary_min", "Salariul minim nu poate fi mai mare decât salariul maxim.")
                    self.add_error("salary_max", "Salariul maxim trebuie să fie mai mare sau egal cu salariul minim.")
            except TypeError:
                pass
        return cleaned

    def clean_description(self):
        desc = self.cleaned_data.get("description") or ""
        # Redact obvious emails/phones
        desc = EMAIL_RE.sub("[redactat-email]", desc)
        desc = PHONE_RE.sub("[redactat-telefon]", desc)
        return desc