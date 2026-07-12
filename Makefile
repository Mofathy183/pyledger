.PHONY: bootstrap install-api install-cli install-core fix pre-push

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