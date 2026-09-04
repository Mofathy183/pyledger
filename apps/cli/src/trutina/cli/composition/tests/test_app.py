import importlib

import pytest
from trutina.cli.composition.app import app
from typer.testing import CliRunner

runner = CliRunner()

_app_module = importlib.import_module("trutina.cli.composition.app")


@pytest.mark.unit
class TestAppHelp:
    def test_exits_zero(self):
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0

    def test_does_not_construct_a_cli_context(self, monkeypatch):
        def _fail_if_called(*args, **kwargs):
            raise AssertionError("build_context() must not be called for --help")

        monkeypatch.setattr(_app_module, "build_context", _fail_if_called)

        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0


@pytest.mark.unit
class TestJournalSubcommandHelp:
    def test_still_exits_zero_and_renders_help(self):
        result = runner.invoke(app, ["journal", "--help"])

        assert result.exit_code == 0
        assert "journal" in result.output.lower()

    def test_main_callback_runs_before_the_subcommands_own_help_exits(self):
        calls = []
        original = _app_module.build_context

        def _tracking(*args, **kwargs):
            calls.append((args, kwargs))
            return original(*args, **kwargs)

        import pytest as _pytest  # local import to keep monkeypatch scoping obvious

        mp = _pytest.MonkeyPatch()
        try:
            mp.setattr(_app_module, "build_context", _tracking)
            result = runner.invoke(app, ["journal", "--help"])
        finally:
            mp.undo()

        assert result.exit_code == 0
        assert len(calls) == 1
