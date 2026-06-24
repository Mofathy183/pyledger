import pytest

from pyledger.config import TestSettings


@pytest.fixture(scope="session")
def test_settings() -> TestSettings:
    return TestSettings()
