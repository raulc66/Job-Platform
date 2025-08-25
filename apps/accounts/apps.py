from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"  # full path
    label = "accounts"      # keeps AUTH_USER_MODEL = 'accounts.User' valid

    def ready(self):
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass