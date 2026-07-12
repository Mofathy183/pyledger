#!/usr/bin/env bash
# Auto-fixes what it safely can (formatting, some lint rules). Run this
# explicitly before pre-push.sh, never as part of the gate itself —
# a gate should report, not rewrite your tree out from under you.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "==> ruff format"
uv run ruff format .

echo "==> ruff check --fix"
uv run ruff check --fix .

echo "Auto-fixes applied. Re-run pre-push.sh to verify."