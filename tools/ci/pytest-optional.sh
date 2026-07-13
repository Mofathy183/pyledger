#!/usr/bin/env bash
# Runs `pytest -m "<marker-expr>" <extra args...>` and treats exit code 5
# ("no tests collected") as success rather than failure.
#
# Why this exists: as packages get scaffolded mid-migration with no tests
# yet for a given layer/speed combination, an empty suite would otherwise
# hard-fail CI. Previously this guard was only applied to integration runs
# and hand-copied per job; this script applies it uniformly to unit and
# integration alike, in one place, so the exit-5 logic can't drift between
# jobs the way hand-copied inline guards do.
#
# Usage:
#   tools/ci/pytest-optional.sh "unit and shared" --cov=pyledger --cov-report=term-missing
#   tools/ci/pytest-optional.sh "integration and core"
set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <marker-expr> [pytest args...]" >&2
    exit 2
fi

marker_expr="$1"
shift

set +e
uv run pytest -m "$marker_expr" "$@"
code=$?
set -e

if [ "$code" -eq 5 ]; then
    echo "No tests collected for marker expression '$marker_expr' — treating as pass."
    exit 0
fi

exit "$code"