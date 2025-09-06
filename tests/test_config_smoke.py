from pathlib import Path
from django.conf import settings
from django.template.loader import get_template

def test_templates_dir_and_home():
    dirs = [Path(p) for p in settings.TEMPLATES[0]["DIRS"]]
    assert any(d.is_dir() for d in dirs), "No template dir exists"
    get_template("home.html")  # should not raise

def test_static_dirs_exist():
    for p in settings.STATICFILES_DIRS:
        assert Path(p).is_dir(), f"Static dir missing: {p}"

def test_user_model_is_custom():
    assert settings.AUTH_USER_MODEL == "accounts.User"
