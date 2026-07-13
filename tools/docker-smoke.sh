#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# QG7 smoke test: builds the production API image, boots it against a
# real MongoDB on an isolated Docker network, and polls GET /health until
# it responds or the retry budget is exhausted.
#
# This is the exact logic CI's QG7 job runs -- run it locally before
# pushing a Dockerfile/compose change rather than waiting on CI to catch
# a broken image (e.g. the missing `packages/` COPY that broke this
# image previously -- this script exists specifically so that class of
# bug fails on a laptop in ~30s, not after a CI round trip).
#
# Usage:
#   tools/docker-smoke.sh
#
# Cleanup (containers + network) always runs via the EXIT trap, whether
# the smoke test passes, fails, or is interrupted (Ctrl-C).

NETWORK="pyledger-smoke-net"
MONGO_NAME="pyledger-smoke-mongo"
API_NAME="pyledger-smoke-api"
IMAGE_TAG="pyledger-api:smoke"
RETRIES=15
RETRY_INTERVAL=2

cleanup() {
    echo "==> Cleaning up smoke test resources"
    docker rm -f "$API_NAME" "$MONGO_NAME" >/dev/null 2>&1 || true
    docker network rm "$NETWORK" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "==> Building image"
tools/docker-build.sh "$IMAGE_TAG"

echo "==> Creating isolated network"
docker network create "$NETWORK" >/dev/null

echo "==> Starting Mongo"
docker run -d --rm \
    --name "$MONGO_NAME" \
    --network "$NETWORK" \
    mongo:8 >/dev/null

echo "==> Waiting for Mongo to accept connections"
for i in $(seq 1 "$RETRIES"); do
    if docker exec "$MONGO_NAME" mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
        break
    fi
    if [ "$i" -eq "$RETRIES" ]; then
        echo "ERROR: Mongo did not become healthy in time" >&2
        exit 1
    fi
    sleep "$RETRY_INTERVAL"
done

echo "==> Starting API"
docker run -d --rm \
    --name "$API_NAME" \
    --network "$NETWORK" \
    -e PYLEDGER_MONGO__URI="mongodb://${MONGO_NAME}:27017" \
    -e PYLEDGER_MONGO__DB="pyledger_smoke" \
    -p 8000:8000 \
    "$IMAGE_TAG" >/dev/null

echo "==> Waiting for API /health"
for i in $(seq 1 "$RETRIES"); do
    if curl -fsS "http://localhost:8000/health" >/dev/null 2>&1; then
        echo "API is healthy"
        exit 0
    fi
    if [ "$i" -eq "$RETRIES" ]; then
        echo "ERROR: API did not become healthy in time" >&2
        echo "==> API logs:" >&2
        docker logs "$API_NAME" >&2 || true
        exit 1
    fi
    sleep "$RETRY_INTERVAL"
done