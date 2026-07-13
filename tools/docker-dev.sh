#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Thin wrapper around `docker compose watch` for the dev-stage API image.
# Zero-setup onboarding path -- no local Python/uv/Mongo install required.
#
# Not the fastest inner loop for a single contributor iterating on the
# API alone; `uv run --package pyledger-api uvicorn pyledger.api.main:app
# --reload` directly on the host will always be faster for that case.
# This exists so the onboarding instruction is one command instead of
# "remember these two -f flags".
#
# Usage:
#   tools/docker-dev.sh

docker compose -f compose.yml -f compose.dev.yml watch