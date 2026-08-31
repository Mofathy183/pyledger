"""Interactive shell loop for the Trutina CLI.

Milestone 2: real dispatch into the existing Typer app. Every typed
line is handed to the same `app` object main.py already dispatches for
one-shot invocations -- there is no second command-parsing path here.

Milestone 4: live-narrowing completion (complete_while_typing=True) and
a themed style matching cli/shared/ui/theme, layered on top of the
Milestone 3 dispatch/exit/slash-handling behavior below, unchanged.

Confirmed empirically (see diag_milestone2.py, not assumed):

- A command that fails at the domain/validation level (AppError,
    ValidationAppError, pydantic.ValidationError) is already fully
    handled by that command's own error_boundary() before control
    returns here -- the panel is printed and app(...) returns normally.
    This loop does nothing extra for that case.
- The only case that raises back to this loop is a genuine Click
    usage error (unknown command, bad/missing flag). This Typer version
    (0.27.2) vendors its own Click fork internally rather than routing
    through the public `click` package, so `click.UsageError` does NOT
    match it -- confirmed via MRO inspection. The public, stable ancestor
    across that whole vendored exception family is
    `typer.exceptions.TyperException`, which is what this module catches.
"""

import shlex

from prompt_toolkit import PromptSession
from prompt_toolkit.input import Input
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.output import Output
from prompt_toolkit.styles import Style
from trutina.cli.app import app
from trutina.cli.shell_builtins import SHELL_BUILTINS
from trutina.cli.shell_completion import build_completer
from trutina.cli.state import CliState
from typer.exceptions import TyperException


def _build_key_bindings() -> KeyBindings:
    """Make Tab accept a match instead of cycling the menu selection.

    prompt_toolkit's default binding treats Tab, once a completion menu
    is already open, as "move to the next match" (the same as Down) --
    with complete_while_typing already keeping the menu open, this
    means Tab never actually completes anything, it just cycles. This
    override restores the expected "Tab completes the word" behavior:
    accept the currently highlighted match, or the first match if none
    is highlighted yet, and close the menu.
    """
    kb = KeyBindings()

    @kb.add(Keys.Tab)
    def _accept_completion(event) -> None:
        buffer = event.current_buffer
        state = buffer.complete_state

        if state is None:
            buffer.start_completion(select_first=True)
            return

        completion = state.current_completion
        if completion is None and state.completions:
            completion = state.completions[0]

        if completion is not None:
            buffer.apply_completion(completion)

    return kb


# Milestone 4 (D7 styling gap): mirrors the palette already used by
# cli/shared/ui/theme/styles.py's ConsoleThemes so the completion menu
# doesn't look like prompt_toolkit's stock chrome. Kept as its own
# small function (rather than inline in run_shell) so it can be swapped
# for a direct THEME_MAP-derived palette later without touching the
# loop itself.
def _shell_style() -> Style:
    """Build the prompt_toolkit Style for the completion menu.

    Colors mirror ConsoleThemes' palette (bold green success, teal
    accent, muted dim text) rather than prompt_toolkit's defaults, so
    the shell's dropdown reads as part of the same CLI, not a bolted-on
    third-party widget.
    """
    return Style.from_dict(
        {
            "completion-menu.completion": "bg:#171a23 #e4e6eb",
            "completion-menu.completion.current": "bg:#262a37 #7dd3c0 bold",
            "completion-menu.meta.completion": "bg:#171a23 #9aa0ae italic",
            "completion-menu.meta.completion.current": "bg:#262a37 #9aa0ae italic",
        }
    )


def run_shell(
    state: CliState,
    *,
    input: Input | None = None,
    output: Output | None = None,
) -> None:
    """Run the interactive shell loop until the user exits.

    Args:
        state: The CliState for this session, threaded through to
            every dispatched command exactly as one-shot invocations
            already do via ``obj=state``.
        input: Override for prompt_toolkit's input source. ``None`` in
            production, which resolves to the real terminal. Tests
            supply a ``create_pipe_input()`` pipe so the session never
            probes for a real console.
        output: Override for prompt_toolkit's output sink. ``None`` in
            production. Tests supply ``DummyOutput()`` for the same
            reason.
    """
    print("Trutina interactive shell. Type 'exit' or 'quit' to leave.")
    session = PromptSession(
        completer=build_completer(),
        complete_while_typing=True,
        style=_shell_style(),
        key_bindings=_build_key_bindings(),
        input=input,
        output=output,
    )

    while True:
        try:
            line = session.prompt("trutina> ")
        except EOFError, KeyboardInterrupt:
            print()
            break

        stripped = line.strip()
        if not stripped:
            continue

        # D6: '/account' and 'account' behave identically -- this
        # includes the shell's own built-ins, not just dispatched
        # commands, so '/exit' and 'exit' must both leave the shell.
        if stripped.startswith("/"):
            stripped = stripped[1:]

        if stripped in SHELL_BUILTINS:
            break

        try:
            args = shlex.split(stripped)
        except ValueError as exc:
            print(f"Could not parse input: {exc}")
            continue

        try:
            app(args, obj=state, standalone_mode=False)
        except TyperException as exc:
            print(str(exc) or type(exc).__name__)
