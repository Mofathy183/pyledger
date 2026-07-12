#!/usr/bin/env bash
# Syncs every workspace member in one resolution pass. This is the
# everyday command for local development — see install-core.sh /
# install-cli.sh / install-api.sh / install-infrastructure.sh for the
# CI-scoped alternative, which exists for per-package CI jobs, not for
# local use.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# Local dev: `bash tools/install-all.sh`       → may update uv.lock
# CI:        `bash tools/install-all.sh --ci`  → fails if lock is stale
mode="${1:-}"
case "$mode" in
    --ci)
        uv sync --all-packages --frozen
        ;;
    "")
        uv sync --all-packages
        ;;
    *)
        echo "Unknown argument: $mode" >&2
        echo "Usage: $0 [--ci]" >&2
        exit 1
        ;;
esac

echo "All workspace members synced."