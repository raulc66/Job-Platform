from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.http import HttpResponse
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
