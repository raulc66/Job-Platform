from pathlib import Path
import os

# Repo root: /home/user/Desktop/Programming/Coding/Proj/Jobs Platform/jobboard
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-unsafe-secret')
DEBUG = os.getenv('DEBUG', '1') == '1'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # local apps
    "apps.accounts",
    "apps.analytics",
    "apps.applications",
    "apps.companies",
    "apps.jobs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "jobboard.urls"
WSGI_APPLICATION = "jobboard.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Correct templates folder (contains home.html)
        "DIRS": [BASE_DIR / "jobboard" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.static",
            ],
        },
    },
]

# Use the custom User to prevent reverse accessor clashes
AUTH_USER_MODEL = "accounts.User"

STATIC_URL = "/static/"
# Correct static source folder
STATICFILES_DIRS = [BASE_DIR / "jobboard" / "static"]
STATIC_ROOT = BASE_DIR / "static_cdn"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"