from unittest.mock import MagicMock

import pytest
from trutina.cli import main as main_module
from trutina.cli.composition.app import app


@pytest.mark.unit
class TestKnownCommands:
    def test_derives_registered_group_names(self):
        assert main_module._known_commands(app) == {"account", "journal", "posting"}


@pytest.mark.unit
class TestHelpFlags:
    def test_derives_help_flags_from_context_settings(self):
        assert main_module._help_flags(app) == {"-h", "--help"}


@pytest.mark.unit
class TestShouldEnterShell:
    def test_bare_invocation_enters_shell(self):
        assert main_module._should_enter_shell([], app) is True

    def test_long_help_flag_does_not_enter_shell(self):
        assert main_module._should_enter_shell(["--help"], app) is False

    def test_short_help_flag_does_not_enter_shell(self):
        assert main_module._should_enter_shell(["-h"], app) is False

    def test_unknown_token_enters_shell(self):
        assert main_module._should_enter_shell(["frobnicate"], app) is True

    @pytest.mark.parametrize("command", ["account", "journal", "posting"])
    def test_known_command_dispatches_normally(self, command):
        assert main_module._should_enter_shell([command, "list"], app) is False

    @pytest.mark.parametrize("command", ["account", "journal", "posting"])
    def test_known_command_with_help_flag_still_dispatches_normally(self, command):
        # e.g. `account --help` -- Typer/Click handles this itself once
        # inside that command's own parsing; it must not be intercepted
        # here as if it were the top-level help flag.
        assert main_module._should_enter_shell([command, "--help"], app) is False


def _fake_context():
    context = MagicMock()

    async def fake_aclose():
        return None

    context.aclose = fake_aclose
    return context


def _fake_group(name: str) -> MagicMock:
    group = MagicMock()
    group.name = name
    return group


@pytest.mark.unit
class TestRunDispatch:
    def test_enters_shell_for_bare_invocation(self, monkeypatch):
        run_shell_mock = MagicMock()
        app_mock = MagicMock()
        monkeypatch.setattr(main_module, "run_shell", run_shell_mock)
        monkeypatch.setattr(main_module, "app", app_mock)
        monkeypatch.setattr("sys.argv", ["trutina-cli"])

        main_module.run(_fake_context())

        run_shell_mock.assert_called_once()
        app_mock.assert_not_called()

    def test_dispatches_to_typer_for_known_command(self, monkeypatch):
        run_shell_mock = MagicMock()
        app_mock = MagicMock()
        app_mock.registered_groups = [
            _fake_group("account"),
            _fake_group("journal"),
            _fake_group("posting"),
        ]
        monkeypatch.setattr(main_module, "run_shell", run_shell_mock)
        monkeypatch.setattr(main_module, "app", app_mock)
        monkeypatch.setattr("sys.argv", ["trutina-cli", "account", "list"])

        main_module.run(_fake_context())

        app_mock.assert_called_once()
        run_shell_mock.assert_not_called()

    def test_dispatches_to_typer_for_top_level_help_flag(self, monkeypatch):
        run_shell_mock = MagicMock()
        app_mock = MagicMock()
        app_mock.registered_groups = []
        app_mock.info.context_settings = {"help_option_names": ["-h", "--help"]}
        monkeypatch.setattr(main_module, "run_shell", run_shell_mock)
        monkeypatch.setattr(main_module, "app", app_mock)
        monkeypatch.setattr("sys.argv", ["trutina-cli", "--help"])

        main_module.run(_fake_context())

        app_mock.assert_called_once()
        run_shell_mock.assert_not_called()
