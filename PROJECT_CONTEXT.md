
Canonical paths and invariants

- Settings module (dev default): jobboard.settings.dev
- Templates dir: jobboard/jobboard/templates (home.html lives here)
- Static source: jobboard/jobboard/static
- Static collect dest: static_cdn/
- Custom user: accounts.User
- Middleware must include: SessionMiddleware, AuthenticationMiddleware, MessageMiddleware
- Apps present: accounts, companies, jobs, applications

Runbook

- Snapshot context: ./tools/context_snapshot.sh
- Django diagnostics: python manage.py diag
- Smoke tests: pytest -q
