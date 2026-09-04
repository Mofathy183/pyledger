import pytest
from trutina.cli.composition.bootstrap import build_context
from trutina.config import get_settings


@pytest.mark.unit
class TestBuildContext:
    def test_propagates_explicit_settings(self, test_settings):
        context = build_context(test_settings)

        assert context._settings is test_settings

    def test_falls_back_to_get_settings_when_omitted(self):
        context = build_context()

        assert context._settings is get_settings()
