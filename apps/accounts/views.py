from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import FormView
from django.contrib import messages
from django.utils import timezone
import json

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


@login_required
def profile_edit(request):
    profile, _ = SeekerProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = SeekerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            # mark ready if essentials present
            if profile.location and profile.skills:
                profile.quick_apply_ready = True
                profile.save(update_fields=["quick_apply_ready"])
            return redirect("accounts:profile_edit")
    else:
        form = SeekerProfileForm(instance=profile)

    # compute completion: essentials (location, skills) + optional (cv, portfolio)
    essentials = 0
    essentials += 1 if profile.location else 0
    essentials += 1 if profile.skills else 0
    optional = 0
    # if you later add CV FileField: optional += 1 if profile.cv else 0
    optional += 1 if getattr(profile, "portfolio_url", "") else 0

    # 70% weight essentials (2 items), 30% optional (2 slots: cv, portfolio)
    essentials_pct = (essentials / 2) * 70
    optional_pct = (optional / 2) * 30
    profile_completion = int(round(essentials_pct + optional_pct))

    ctx = {
        "form": form,
        "profile": profile,
        "profile_completion": profile_completion,
        "has_location": bool(profile.location),
        "has_skills": bool(profile.skills),
        "has_cv": bool(getattr(profile, "cv", None)),  # safe if not present
        "has_portfolio": bool(getattr(profile, "portfolio_url", "")),
    }
    return render(request, "accounts/profile_edit.html", ctx)


@login_required
@require_POST
def quick_apply_prep(request):
    # Accept JSON with location and skills, mark quick_apply_ready
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    location = (data.get("location") or "").strip()
    skills = (data.get("skills") or "").strip()

    profile, _ = SeekerProfile.objects.get_or_create(user=request.user)
    changed = False
    if location and location != (profile.location or ""):
        profile.location = location
        changed = True
    if skills and skills != (profile.skills or ""):
        # normalize to at most 3 skills
        sk = [s.strip() for s in skills.split(",") if s.strip()][:3]
        profile.skills = ", ".join(sk)
        changed = True

    if location and profile.skills:
        profile.quick_apply_ready = True
        changed = True

    if changed:
        profile.save()

    return JsonResponse({"ok": True, "quick_apply_ready": profile.quick_apply_ready})