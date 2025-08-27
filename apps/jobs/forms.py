from django import forms
from .models import Job


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = "__all__"

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