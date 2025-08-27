from django import forms
from .models import Application

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["cover_letter", "cv"]
        labels = {
            "cover_letter": "Scrisoare de intenție (opțional)",
            "cv": "CV (PDF/DOC/DOCX, opțional)",
        }
        widgets = {
            "cover_letter": forms.Textarea(attrs={"rows": 6, "placeholder": "Scrie un mesaj (opțional)"}),
            "cv": forms.ClearableFileInput(attrs={"accept": ".pdf,.doc,.docx"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cover_letter"].required = False
        self.fields["cv"].required = False

    def clean_cv(self):
        cv = self.cleaned_data.get("cv")
        if not cv:
            return None
        # Tipuri permise
        allowed = {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        content_type = getattr(cv, "content_type", None)
        if content_type and content_type not in allowed:
            raise forms.ValidationError("Tip fișier neacceptat. Încarcă un PDF, DOC sau DOCX.")
        # Dimensiune maximă 5 MB
        max_mb = 5
        if cv.size > max_mb * 1024 * 1024:
            raise forms.ValidationError(f"Fișierul este prea mare. Dimensiunea maximă este {max_mb} MB.")
        return cv