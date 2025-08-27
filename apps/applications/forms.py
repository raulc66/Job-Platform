from django import forms
from .models import Application

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["cover_letter", "cv"]
        labels = {
            "cover_letter": "Scrisoare de intenție (opțional)",
            "cv": "CV (PDF sau DOCX, opțional)",
        }
        widgets = {
            "cover_letter": forms.Textarea(attrs={"rows": 6, "placeholder": "Scrie un mesaj (opțional)"}),
            "cv": forms.ClearableFileInput(attrs={"accept": ".pdf,.docx"}),
        }
        help_texts = {
            "cv": "Formate acceptate: PDF, DOCX. Dimensiune maximă: 4 MB. CV-ul și scrisoarea sunt opționale.",
            "cover_letter": "Opțional. Poți lăsa gol.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cover_letter"].required = False
        self.fields["cv"].required = False

    def clean_cv(self):
        cv = self.cleaned_data.get("cv")
        if not cv:
            return None

        # Accept only PDF and DOCX
        allowed_mimes = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        # Fallback by extension if content_type missing or unreliable
        name_lower = getattr(cv, "name", "").lower()
        ok_ext = name_lower.endswith(".pdf") or name_lower.endswith(".docx")
        content_type = getattr(cv, "content_type", None)

        if content_type:
            if content_type not in allowed_mimes:
                raise forms.ValidationError("Tip fișier neacceptat. Încarcă un PDF sau DOCX.")
        elif not ok_ext:
            raise forms.ValidationError("Tip fișier neacceptat. Încarcă un PDF sau DOCX.")

        # Max 4 MB
        max_mb = 4
        if cv.size and cv.size > max_mb * 1024 * 1024:
            raise forms.ValidationError(f"Fișierul este prea mare. Dimensiunea maximă este {max_mb} MB.")

        return cv