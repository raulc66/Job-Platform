from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


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
