import io
import os
import sys
from pathlib import Path

from django import get_version as django_version
from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.template import engines
from django.urls import get_resolver

class Command(BaseCommand):
    help = "Print a concise snapshot of Django config (paths, templates, static, auth user, middleware, urls, migrations)."

    def handle(self, *args, **options):
        out = self.stdout
        err = self.stderr

        out.write("== Runtime ==")
        out.write(f"Python: {sys.version.split()[0]}")
        out.write(f"Django: {django_version()}")
        out.write("")

        out.write("== Settings ==")
        out.write(f"SETTINGS_MODULE: {settings.SETTINGS_MODULE}")
        out.write(f"BASE_DIR: {settings.BASE_DIR}")
        out.write(f"AUTH_USER_MODEL: {settings.AUTH_USER_MODEL}")
        out.write("MIDDLEWARE has sessions/auth/messages: " +
                  str((
                      "django.contrib.sessions.middleware.SessionMiddleware" in settings.MIDDLEWARE,
                      "django.contrib.auth.middleware.AuthenticationMiddleware" in settings.MIDDLEWARE,
                      "django.contrib.messages.middleware.MessageMiddleware" in settings.MIDDLEWARE,
                  )))
        out.write("")

        out.write("== Templates ==")
        tpl_dirs = [Path(p) for p in settings.TEMPLATES[0]["DIRS"]]
        for d in tpl_dirs:
            out.write(f"- {d} exists={d.is_dir()} home.html={ (d / 'home.html').exists() }")
        try:
            engines["django"].get_template("home.html")
            out.write("Resolve: home.html OK")
        except Exception as e:
            out.write(f"Resolve: home.html FAIL ({e.__class__.__name__})")
        out.write("")

        out.write("== Static ==")
        static_dirs = [Path(p) for p in settings.STATICFILES_DIRS]
        for d in static_dirs:
            out.write(f"- {d} exists={d.is_dir()}")
        out.write(f"STATIC_ROOT: {settings.STATIC_ROOT} (exists={Path(settings.STATIC_ROOT).is_dir()})")
        out.write("")

        out.write("== URLs ==")
        try:
            resolver = get_resolver()
            patterns = getattr(resolver, "url_patterns", [])
            out.write(f"Root url patterns: {len(patterns)}")
            named = sorted([n for n in resolver.reverse_dict if isinstance(n, str)])
            out.write(f"Named urls (sample): {', '.join(named[:20])}{' ...' if len(named) > 20 else ''}")
        except Exception as e:
            err.write(f"URL inspection error: {e}")
        out.write("")

        out.write("== Database ==")
        db = settings.DATABASES.get("default", {})
        out.write(f"ENGINE: {db.get('ENGINE')}")
        out.write(f"NAME: {db.get('NAME')}")
        out.write("")

        out.write("== Apps (installed) ==")
        out.write(", ".join(a for a in settings.INSTALLED_APPS if a.startswith("apps.") or a.startswith("django.")))
        out.write("")

        out.write("== Migrations (summary) ==")
        buf = io.StringIO()
        try:
            call_command("showmigrations", stdout=buf, verbosity=0)
            for line in buf.getvalue().splitlines():
                if line.strip().startswith("apps.") or line.strip().startswith("accounts") or line.strip().startswith("jobs") or line.strip().startswith("applications") or line.strip().startswith("companies"):
                    out.write(line)
        except Exception as e:
            err.write(f"showmigrations error: {e}")
        out.write("")
