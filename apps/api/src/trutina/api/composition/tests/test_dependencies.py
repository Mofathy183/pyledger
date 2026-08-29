"""Unit tests for the per-service dependency providers.

Each provider is a one-line pass-through (`request.app.state.container.<attr>`)
per dependencies.py's own docstring. These tests confirm exactly that —
nothing about FastAPI's Depends() injection mechanism itself, which is
framework machinery, not Trutina code.
"""

from types import SimpleNamespace
from typing import cast

import pytest
from fastapi import Request
from trutina.api.composition.dependencies import (
    get_account_service,
    get_journal_service,
    get_posting_service,
    get_settings_dep,
)
from trutina.config import get_settings


def _make_request(container: object) -> Request:
    """A minimal stand-in for fastapi.Request exposing only what the
    providers actually read: request.app.state.container.

    Each provider is a synchronous attribute pass-through (see
    dependencies.py's own docstring) — it never touches any other
    Request behavior (headers, body, scope, etc.), so a SimpleNamespace
    exposing only the read attributes is sufficient at runtime.
    `cast()` tells the type checker this stand-in is being used as a
    Request on purpose, rather than fabricating a real ASGI scope for a
    test that doesn't need one.
    """
    fake = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(container=container))
    )
    return cast(Request, fake)


@pytest.mark.unit
class TestGetAccountService:
    def test_returns_container_account_service(self):
        container = SimpleNamespace(account_service="the-account-service")
        request = _make_request(container)

        result = get_account_service(request)

        assert result == "the-account-service"


@pytest.mark.unit
class TestGetJournalService:
    def test_returns_container_journal_service(self):
        container = SimpleNamespace(journal_service="the-journal-service")
        request = _make_request(container)

        result = get_journal_service(request)

        assert result == "the-journal-service"


@pytest.mark.unit
class TestGetPostingService:
    def test_returns_container_posting_service(self):
        container = SimpleNamespace(posting_service="the-posting-service")
        request = _make_request(container)

        result = get_posting_service(request)

        assert result == "the-posting-service"


@pytest.mark.unit
class TestGetSettingsDep:
    def test_returns_api_settings_off_get_settings(self):
        """isolate_settings_cache (tests/fixtures/settings.py) is
        autouse=True and clears get_settings.cache_clear() before and
        after every test, so both calls below resolve against the same
        freshly-cached Settings instance without extra setup here.
        """
        result = get_settings_dep()

        assert result == get_settings().api
