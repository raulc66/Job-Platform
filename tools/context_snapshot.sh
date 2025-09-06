#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OUT="context/snapshot-$(date +%Y%m%d-%H%M%S).txt"
mkdir -p context

{
  echo "== Git =="
  git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no git"
  git status -s 2>/dev/null || true
  git rev-parse HEAD 2>/dev/null || true
  echo

  echo "== Tree (top) =="
  ls -la
  echo

  echo "== Python/Django/Deps =="
  source env/bin/activate 2>/dev/null || true
  python -V 2>/dev/null || true
  python -c "import django, sys; print('Django', django.get_version())" 2>/dev/null || true
  pip freeze 2>/dev/null | sed -n '1,120p' || true
  echo

  echo "== Django diag =="
  python manage.py diag 2>&1 || true
  echo

  echo "== Settings grep (safety) =="
  grep -Rni \"STATICFILES_DIRS\\|TEMPLATES =\\|AUTH_USER_MODEL\" jobboard/settings || true
  echo
} | tee "$OUT"

echo "Snapshot saved to $OUT"