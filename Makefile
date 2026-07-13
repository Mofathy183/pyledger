.PHONY: bootstrap install-api install-cli install-core fix pre-push docker-build docker-smoke docker-dev

bootstrap:
	bash tools/bootstrap.sh

install-core:
	uv sync --package pyledger-core

install-cli:
	uv sync --package pyledger-cli

install-api:
	uv sync --package pyledger-api

fix:
	bash tools/fix.sh

pre-push:
	bash tools/pre-push.sh

docker-build:
	bash tools/docker-build.sh

docker-smoke:
	bash tools/docker-smoke.sh

docker-dev:
	bash tools/docker-dev.sh