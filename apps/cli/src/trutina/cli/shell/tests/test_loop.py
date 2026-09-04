import pytest
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput
from trutina.cli.shell import run_shell


def _run_with_inputs(state, lines: list[str]) -> None:
    """Feed scripted lines through a real prompt_toolkit pipe input.

    Closing the pipe after sending the given lines means: if the
    shell reaches the end of the scripted lines without hitting
    'exit'/'quit', the next session.prompt() call raises EOFError --
    exercising the exact same code path a real Ctrl-D would, and
    letting an empty `lines` list stand in for "immediate EOF"
    (see TestShellExit.test_eof_ends_loop_cleanly).
    """
    text = "".join(f"{line}\n" for line in lines)
    with create_pipe_input() as pipe_input:
        pipe_input.send_text(text)
        pipe_input.close()
        run_shell(state, input=pipe_input, output=DummyOutput())


@pytest.mark.unit
class TestShellExit:
    def test_exit_keyword_ends_loop(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, ["exit"])

    def test_quit_keyword_ends_loop(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, ["quit"])

    def test_eof_ends_loop_cleanly(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, [])

    def test_slash_prefixed_exit_also_ends_loop(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, ["/exit"])

    def test_slash_prefixed_quit_also_ends_loop(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, ["/quit"])


@pytest.mark.unit
class TestShellDispatch:
    def test_known_command_runs_without_raising(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, ["account list", "quit"])

    def test_leading_slash_is_stripped_before_dispatch(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, ["/account list", "quit"])

    def test_unknown_command_does_not_exit_the_loop(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, ["not-a-real-command", "quit"])

    def test_blank_line_is_ignored(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, ["", "   ", "quit"])


@pytest.mark.unit
class TestShellHelp:
    def test_bare_help_does_not_exit_the_loop(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, ["help", "quit"])

    def test_slash_prefixed_help_does_not_exit_the_loop(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, ["/help", "quit"])

    def test_help_for_a_command_group_does_not_exit_the_loop(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, ["help account", "quit"])

    def test_help_for_a_subcommand_does_not_exit_the_loop(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, ["help journal create", "quit"])

    def test_help_for_unknown_target_does_not_crash_the_loop(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, ["help nonsense", "quit"])


@pytest.mark.unit
class TestShellTrailingHelp:
    """`<command...> help` -- the shorthand shell_completion.py now
    offers as a completion must actually dispatch correctly, not just
    autocomplete.
    """

    def test_trailing_help_after_group_does_not_exit_the_loop(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, ["account help", "quit"])

    def test_trailing_help_after_subcommand_does_not_exit_the_loop(
        self, fake_cli_state
    ):
        _run_with_inputs(fake_cli_state, ["journal create help", "quit"])

    def test_slash_prefixed_trailing_help_does_not_exit_the_loop(self, fake_cli_state):
        _run_with_inputs(fake_cli_state, ["/account list help", "quit"])

    def test_trailing_help_for_unknown_group_does_not_crash_the_loop(
        self, fake_cli_state
    ):
        _run_with_inputs(fake_cli_state, ["nonsense help", "quit"])
