"""Interactive shell loop for the Trutina CLI.

This module owns the loop and nothing else: read a line, decide what
kind of line it is (blank, a built-in, a help shorthand, or a real
command), and hand it to shell/dispatch.py to actually run. Everything
that used to live inline here has its own file now:

- shell/builtins.py    -- exit/quit/help catalog + terminating_keywords()
- shell/completion.py  -- the Tab/live-narrowing completion tree
- shell/keybindings.py -- the Tab-accepts-completion override
- shell/dispatch.py    -- turning a line into a real app(...) call
- cli/shared/ui/       -- everything the user actually *sees*: the
    welcome banner (shell_banner.py, logo.py) and the prompt/
    completion-menu colors (shell_style.py)

D6: '/account' and 'account' behave identically, including the
shell's own built-ins -- '/exit'/'exit' and '/help'/'help' must both
behave the same way. The leading '/' is stripped once, here, before
any of the checks below run.

Help shorthand: both `help <command...>` (leading) and
`<command...> help` (trailing) are shorthand for `<command...> --help`,
resolved by dispatch.run_help() through the same `app(...)` call every
other line goes through -- reusing Typer/Click's own help rendering
rather than authoring a second copy of that text here, the same "one
source of truth" reasoning already applied to completion descriptions
(D7). shell/completion.py offers both shorthands as completions so
neither has to be memorized. Only `exit`/`quit` end the loop; `help`
prints and continues -- see shell/builtins.py's `terminating_keywords()`.
"""

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.input import Input
from prompt_toolkit.output import Output
from trutina.cli.composition.state import CliState
from trutina.cli.shared.ui import print_welcome_banner
from trutina.cli.shared.ui.theme import build_shell_style

from .builtins import terminating_keywords
from .completion import build_completer
from .dispatch import dispatch, parse_line, run_help
from .keybindings import build_key_bindings


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
    print_welcome_banner()
    session = PromptSession(
        completer=build_completer(),
        complete_while_typing=True,
        style=build_shell_style(),
        key_bindings=build_key_bindings(),
        input=input,
        output=output,
    )
    prompt_text = FormattedText([("class:prompt", "trutina> ")])
    terminators = terminating_keywords()

    while True:
        try:
            line = session.prompt(prompt_text)
        except EOFError, KeyboardInterrupt:
            print()
            break

        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("/"):
            stripped = stripped[1:]

        if stripped in terminators:
            break

        # Leading `help <target...>` shorthand.
        if stripped == "help" or stripped.startswith("help "):
            run_help(state, stripped.split()[1:])
            continue

        args = parse_line(stripped)
        if args is None:
            continue

        # Trailing `<target...> help` shorthand -- e.g. `account help`,
        # `journal create help` -- equivalent to the leading form
        # above. shell/completion.py offers this as a completion
        # alongside real subcommands so neither form has to be
        # memorized.
        if args and args[-1] == "help":
            run_help(state, args[:-1])
            continue

        dispatch(state, args)
