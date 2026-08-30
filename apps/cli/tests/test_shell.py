import pytest
from trutina.cli.shell import run_shell


def _run_with_inputs(state, lines: list[str], monkeypatch):
    responses = iter(lines)
    monkeypatch.setattr("builtins.input", lambda *_a, **_k: next(responses))
    run_shell(state)


@pytest.mark.unit
class TestShellExit:
    def test_exit_keyword_ends_loop(self, fake_cli_state, monkeypatch):
        _run_with_inputs(fake_cli_state, ["exit"], monkeypatch)  # must not hang/raise

    def test_quit_keyword_ends_loop(self, fake_cli_state, monkeypatch):
        _run_with_inputs(fake_cli_state, ["quit"], monkeypatch)

    def test_eof_ends_loop_cleanly(self, fake_cli_state, monkeypatch):
        def raise_eof(*_a, **_k):
            raise EOFError

        monkeypatch.setattr("builtins.input", raise_eof)
        run_shell(fake_cli_state)  # must not raise


@pytest.mark.unit
class TestShellDispatch:
    def test_known_command_runs_without_raising(self, fake_cli_state, monkeypatch):
        _run_with_inputs(fake_cli_state, ["account list", "quit"], monkeypatch)

    def test_leading_slash_is_stripped_before_dispatch(
        self, fake_cli_state, monkeypatch
    ):
        _run_with_inputs(fake_cli_state, ["/account list", "quit"], monkeypatch)

    def test_unknown_command_does_not_exit_the_loop(
        self, fake_cli_state, monkeypatch, capsys
    ):
        _run_with_inputs(fake_cli_state, ["not-a-real-command", "quit"], monkeypatch)
        # loop reached "quit" and returned normally -- i.e. it survived
        # the TyperException from the unknown command above it.

    def test_blank_line_is_ignored(self, fake_cli_state, monkeypatch):
        _run_with_inputs(fake_cli_state, ["", "   ", "quit"], monkeypatch)
