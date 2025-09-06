from django import forms

class ApplicationForm(forms.Form):
    cover_letter = forms.CharField(
        label="Scrisoare de intenție",
        widget=forms.Textarea(attrs={"rows": 6, "placeholder": "Optional"}),
        required=False,
        max_length=10000,
    )
    cv = forms.FileField(label="CV (PDF/DOC/DOCX, max 4MB)", required=False)

    MAX_SIZE = 4 * 1024 * 1024
    ALLOWED_CONTENT_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    ALLOWED_EXTS = {"pdf", "doc", "docx"}

    def clean_cv(self):
        f = self.cleaned_data.get("cv")
        if not f:
            return f

        # Size
        if f.size and f.size > self.MAX_SIZE:
            raise forms.ValidationError("Fișierul este prea mare (maxim 4MB).")

        # Content type
        ctype = getattr(f, "content_type", None)
        if ctype and ctype not in self.ALLOWED_CONTENT_TYPES:
            raise forms.ValidationError("Tip de fișier neacceptat. Folosește PDF/DOC/DOCX.")

        # Extension fallback
        name = getattr(f, "name", "") or ""
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext and ext not in self.ALLOWED_EXTS:
            raise forms.ValidationError("Extensie neacceptată. Folosește PDF/DOC/DOCX.")

        return f