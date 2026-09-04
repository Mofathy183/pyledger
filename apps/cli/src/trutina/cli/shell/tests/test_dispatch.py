import pytest
from trutina.cli.shared.ui import console
from trutina.cli.shell.dispatch import dispatch, parse_line, run_help


@pytest.mark.unit
class TestParseLine:
    def test_splits_a_simple_line(self):
        assert parse_line("account list") == ["account", "list"]

    def test_splits_quoted_arguments(self):
        assert parse_line('account create --name "Cash Account"') == [
            "account",
            "create",
            "--name",
            "Cash Account",
        ]

    def test_returns_none_and_warns_on_unbalanced_quotes(self):
        with console.capture() as capture:
            result = parse_line('account create --name "unterminated')

        assert result is None
        assert "Could not parse input" in capture.get()


@pytest.mark.unit
class TestDispatch:
    def test_runs_a_known_command_without_raising(self, fake_cli_state):
        # "account list" against an empty fake repo -- the command's own
        # formatter renders an empty-state message via the shared
        # console. dispatch() itself must not raise or print a warning.
        with console.capture() as capture:
            dispatch(fake_cli_state, ["account", "list"])

        assert "Could not parse input" not in capture.get()

    def test_domain_validation_failure_is_rendered_by_its_own_error_boundary(
        self, fake_cli_state
    ):
        # "account get 9999" for a code that doesn't exist -- the
        # command's own error_boundary() catches AppError and renders
        # the panel; dispatch()'s TyperException handler must not fire
        # a second time on top of it.
        with console.capture() as capture:
            dispatch(fake_cli_state, ["account", "get", "9999"])

        assert "Validation Error" in capture.get()

    def test_unknown_command_prints_a_warning_and_does_not_raise(self, fake_cli_state):
        with console.capture() as capture:
            dispatch(fake_cli_state, ["not-a-real-command"])

        assert capture.get().strip() != ""


@pytest.mark.unit
class TestRunHelp:
    def test_top_level_help_does_not_raise(self, fake_cli_state):
        run_help(fake_cli_state, [])

    def test_help_for_a_group_does_not_raise(self, fake_cli_state):
        run_help(fake_cli_state, ["account"])

    def test_help_for_a_subcommand_does_not_raise(self, fake_cli_state):
        run_help(fake_cli_state, ["journal", "create"])

    def test_unknown_target_prints_a_warning_and_does_not_raise(self, fake_cli_state):
        with console.capture() as capture:
            run_help(fake_cli_state, ["nonsense"])

        assert capture.get().strip() != ""
