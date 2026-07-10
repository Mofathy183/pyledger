"""Tests for create_app()'s factory behavior.

Unit tests verify factory construction, settings propagation, and
independence between app instances — no I/O, no lifespan entered.
Integration tests verify the real lifespan actually serves a request
end to end via real_api_client.

Does NOT re-verify FastAPI's own routing/OpenAPI generation, and does
NOT re-verify service business behavior (see modules/*/tests/) or
build_container()'s wiring (see test_container.py).
"""

import pytest
from fastapi import FastAPI

from pyledger.api.composition.app import create_app


@pytest.mark.unit
class TestCreateApp:
    def test_returns_fastapi_instance(self, test_settings):
        app = create_app(test_settings)

        assert isinstance(app, FastAPI)

    def test_uses_settings_title(self, test_settings):
        settings = test_settings.model_copy(deep=True)
        settings.api.title = "Custom Title"

        app = create_app(settings)

        assert app.title == "Custom Title"

    def test_uses_settings_version(self, test_settings):
        settings = test_settings.model_copy(deep=True)
        settings.api.version = "9.9.9"

        app = create_app(settings)

        assert app.version == "9.9.9"

    def test_uses_settings_description(self, test_settings):
        settings = test_settings.model_copy(deep=True)
        settings.api.description = "Custom description"

        app = create_app(settings)

        assert app.description == "Custom description"

    def test_two_calls_produce_independent_app_instances(self, test_settings):
        settings = test_settings.model_copy(deep=True)

        first = create_app(settings)
        second = create_app(settings)

        assert first is not second

    def test_independent_apps_do_not_share_state_container(self, test_settings):
        """Guards the Beanie global-registration isolation concern named
        in create_app()'s own docstring: two app instances must not leak
        mutable state (e.g. app.state.container) between each other.
        """
        settings = test_settings.model_copy(deep=True)

        first = create_app(settings)
        second = create_app(settings)

        first.state.container = object()

        assert not hasattr(second.state, "container")

    def test_falls_back_to_get_settings_when_none_provided(self, test_settings):
        """create_app(settings=None) must not raise — it resolves via
        get_settings() exactly like build_context() does for the CLI.

        isolate_settings_cache (tests/fixtures/settings.py) is
        autouse=True, so get_settings.cache_clear() has already run
        before this test without needing to be requested explicitly.
        """
        app = create_app()

        assert isinstance(app, FastAPI)
