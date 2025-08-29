from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.contrib import messages

from .forms import LoginForm, SignupForm, SeekerProfileForm
from .models import SeekerProfile


class LoginView(DjangoLoginView):
    form_class = LoginForm
    template_name = "account/login.html"  # reuse allauth template


class LogoutView(DjangoLogoutView):
    next_page = reverse_lazy(getattr(settings, "LOGOUT_REDIRECT_URL", "jobs:list"))


class SignupView(FormView):
    form_class = SignupForm
    template_name = "account/signup.html"  # reuse allauth template
    success_url = reverse_lazy(getattr(settings, "LOGIN_REDIRECT_URL", "jobs:list"))

    def form_valid(self, form):
        user = form.save()
        login(
            self.request,
            user,
            backend="allauth.account.auth_backends.AuthenticationBackend",
        )
        return redirect(self.get_success_url())


@login_required
def quick_profile(request):
    profile, _ = SeekerProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = SeekerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil salvat.")
            return redirect("applications:mine")
    else:
        form = SeekerProfileForm(instance=profile)
    return render(request, "accounts/quick_profile.html", {"form": form})