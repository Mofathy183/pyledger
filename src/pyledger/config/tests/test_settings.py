import pytest

from pyledger.config import Settings, get_settings


@pytest.mark.unit
class TestSettings:
    def test_uses_default_values(self):
        settings = Settings()

        assert settings.mongo.uri == "mongodb://localhost:27017"
        assert settings.mongo.db == "pyledger"

    def test_get_settings_returns_cached_instance(self):
        get_settings.cache_clear()

        first = get_settings()
        second = get_settings()

        assert first is second
