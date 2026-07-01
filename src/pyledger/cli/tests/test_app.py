import pytest
from typer.testing import CliRunner

from pyledger.cli.app import app

runner = CliRunner()


@pytest.mark.unit
class TestAppHelp:
    def test_exits_zero(self):
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0

    def test_does_not_construct_a_cli_context(self, monkeypatch):
        def _fail_if_called(*args, **kwargs):
            raise AssertionError("build_context() must not be called for --help")

        monkeypatch.setattr(
            "pyledger.cli.app.build_context",
            _fail_if_called,
        )

        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0


@pytest.mark.unit
class TestJournalSubcommandHelp:
    def test_does_not_construct_a_cli_context(self, monkeypatch):
        def _fail_if_called(*args, **kwargs):
            raise AssertionError("build_context() must not be called for --help")

        monkeypatch.setattr(
            "pyledger.cli.bootstrap.build_context",
            _fail_if_called,
        )

        result = runner.invoke(app, ["journal", "--help"])

        print(result)

        assert result.exit_code == 0
