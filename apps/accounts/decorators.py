from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
import time


def role_required(*roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if hasattr(request.user, "role") and request.user.role in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped
    return decorator


from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin  # noqa: E402


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles: tuple[str, ...] = tuple()

    def test_func(self):
        user = self.request.user
        return bool(getattr(user, "role", None) in self.allowed_roles)


class EmployerRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("employer",)


class SeekerRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("seeker",)


def rate_limit(key="rl", rate=5, period=60):
    """
    Limit a view to `rate` requests per `period` seconds per user/IP.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            ident = request.user.id if request.user.is_authenticated else request.META.get("REMOTE_ADDR", "anon")
            bucket = int(time.time() // period)
            cache_key = f"{key}:{ident}:{bucket}"
            count = cache.get(cache_key, 0)
            if count >= rate:
                return HttpResponse("Prea multe cereri. Încearcă mai târziu.", status=429)
            cache.set(cache_key, count + 1, timeout=period)
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def _has_company(user):
    prof = getattr(user, "employerprofile", None)
    return bool(getattr(prof, "company", None))


def _is_employer(user):
    # Be tolerant to different schemas: role or boolean flag
    role = getattr(user, "role", None)
    return role == "employer" or bool(getattr(user, "is_employer", False))


def employer_required(view=None, *, require_company=True):
    """
    Function-view guard: requires authenticated employer, and optionally a linked company.
    Redirects to companies:employer_setup if company missing.
    """
    def decorator(func):
        @wraps(func)
        def _wrapped(request, *args, **kwargs):
            u = request.user
            if not u.is_authenticated:
                login_url = reverse("accounts:login")
                return redirect(f"{login_url}?next={request.get_full_path()}")
            if not _is_employer(u):
                messages.error(request, "Trebuie să fii angajator pentru a accesa această pagină.")
                return redirect("home")
            if require_company and not _has_company(u):
                messages.info(request, "Asociază o companie înainte de a publica sau edita joburi.")
                return redirect("companies:employer_setup")
            return func(request, *args, **kwargs)
        return _wrapped
    return decorator if view is None else decorator(view)


class EmployerRequiredMixin:
    """
    Class-based view mixin for Job create/update; set require_company=False if needed.
    """
    require_company = True
    def dispatch(self, request, *args, **kwargs):
        u = request.user
        if not u.is_authenticated:
            login_url = reverse("accounts:login")
            return redirect(f"{login_url}?next={request.get_full_path()}")
        if not _is_employer(u):
            messages.error(request, "Trebuie să fii angajator pentru a accesa această pagină.")
            return redirect("home")
        if self.require_company and not _has_company(u):
            messages.info(request, "Asociază o companie înainte de a publica sau edita joburi.")
            return redirect("companies:employer_setup")
        return super().dispatch(request, *args, **kwargs)
