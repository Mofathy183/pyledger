import pytest

from pyledger.config import TestSettings, get_settings


@pytest.fixture(scope="session")
def test_settings() -> TestSettings:
    return TestSettings()


@pytest.fixture(autouse=True)
def isolate_settings_cache():
    """Clear the settings cache before and after every test.

    get_settings() uses lru_cache, which persists across tests.
    Without this fixture, a test that modifies environment variables
    via monkeypatch may corrupt the cached settings seen by later tests.
    """
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
