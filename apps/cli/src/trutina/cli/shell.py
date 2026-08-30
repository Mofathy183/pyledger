"""Interactive shell loop for the Trutina CLI.

Milestone 2: real dispatch into the existing Typer app. Every typed
line is handed to the same `app` object main.py already dispatches for
one-shot invocations -- there is no second command-parsing path here.

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

from trutina.cli.app import app
from trutina.cli.state import CliState
from typer.exceptions import TyperException


def run_shell(state: CliState) -> None:
    """Run the interactive shell loop until the user exits.

    Args:
        state: The CliState for this session, threaded through to
            every dispatched command exactly as one-shot invocations
            already do via ``obj=state``.
    """
    print("Trutina interactive shell. Type 'exit' or 'quit' to leave.")
    while True:
        try:
            line = input("trutina> ")
        except EOFError, KeyboardInterrupt:
            print()
            break

        stripped = line.strip()
        if stripped in ("exit", "quit"):
            break
        if not stripped:
            continue

        # D6: both "/account create" and "account create" work
        # identically -- strip the leading slash before dispatch.
        if stripped.startswith("/"):
            stripped = stripped[1:]

        try:
            args = shlex.split(stripped)
        except ValueError as exc:
            print(f"Could not parse input: {exc}")
            continue

        try:
            app(args, obj=state, standalone_mode=False)
        except TyperException as exc:
            print(str(exc) or type(exc).__name__)
