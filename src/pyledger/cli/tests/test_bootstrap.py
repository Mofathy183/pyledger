"""Unit tests for bootstrap.build_context().

Protects settings propagation into the constructed CliContext -- the
only behavior build_context() owns. A regression here (e.g. `settings
or get_settings()` silently becoming `settings and get_settings()`)
would break every test relying on TestSettings reaching the context,
without any other test currently catching it.
"""

import pytest

from pyledger.cli.bootstrap import build_context
from pyledger.config import get_settings


@pytest.mark.unit
class TestBuildContext:
    def test_propagates_explicit_settings(self, test_settings):
        context = build_context(test_settings)

        assert context._settings is test_settings

    def test_falls_back_to_get_settings_when_omitted(self):
        context = build_context()

        assert context._settings is get_settings()
