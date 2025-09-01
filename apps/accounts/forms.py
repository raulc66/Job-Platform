from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import SeekerProfile

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"autofocus": True, "class": "form-control"}))
    password = forms.CharField(strip=False, widget=forms.PasswordInput(attrs={"class": "form-control"}))


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if hasattr(user, "phone"):
            user.phone = self.cleaned_data.get("phone", "")
        if commit:
            user.save()
        return user


class SeekerProfileForm(forms.ModelForm):
    class Meta:
        model = SeekerProfile
        fields = ["location", "skills", "portfolio_url"]  # CV optional handled separately if you add a FileField
        labels = {
            "location": "Locație",
            "skills": "Aptitudini (maxim 3 recomandat, separate prin virgule)",
            "portfolio_url": "Link portofoliu (opțional)",
        }