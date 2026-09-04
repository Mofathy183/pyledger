"""Console-script entry point for the Trutina CLI.

This is the only place in the application that opens the CLI's single
event loop, via ``start_blocking_portal()``. No command, service, or
repository may create a second loop -- there is exactly one, for the
life of the process.
"""

import sys

from anyio.from_thread import start_blocking_portal
from trutina.cli.composition import CliContext, CliState, app, build_context
from trutina.cli.shell import run_shell


def _known_commands(typer_app) -> set[str]:
    """Return the top-level command/group names Typer will dispatch directly.

    Derived from ``typer_app.registered_groups`` so a new feature (a
    future ``reporting`` group, say) is picked up automatically --
    nothing here needs to change when app.py registers a new group.
    """
    return {group.name for group in typer_app.registered_groups if group.name}


def _help_flags(typer_app) -> set[str]:
    """Return the flag strings that trigger Typer/Click's own help output.

    Derived from ``typer_app.info.context_settings["help_option_names"]``
    -- the same setting app.py already declares
    (``context_settings={"help_option_names": ["-h", "--help"]}``) --
    rather than a second, hand-maintained ``{"--help", "-h"}`` literal
    here that could silently drift out of sync with app.py's own
    configuration.
    """
    context_settings = typer_app.info.context_settings or {}
    return set(context_settings.get("help_option_names", ["--help"]))


def _should_enter_shell(argv: list[str], typer_app) -> bool:
    """Decide whether argv should drop into the shell or dispatch normally.

    Revised from the plan's original D1: a bare invocation enters the
    shell, matching the ``claude``/``codex``/``mongosh`` pattern. A
    help flag (``--help``/``-h``) no longer enters the shell -- it
    dispatches straight to Typer so the top-level usage text prints
    and the process exits immediately, the same way those tools'
    ``--help`` behaves. Only a first token that isn't a registered
    command name (and isn't a help flag) falls through to the shell.
    A recognized command name (``account``, etc.) always dispatches
    normally, including ``account --help``, which Typer/Click handles
    on its own once inside that command's parsing.
    """
    if not argv:
        return True
    if argv[0] in _help_flags(typer_app):
        return False
    return argv[0] not in _known_commands(typer_app)


def run(context: CliContext, *, backend: str = "asyncio") -> None:
    """Dispatch either into the shell or into Typer, and guarantee cleanup."""
    with start_blocking_portal(backend=backend) as portal:
        state = CliState(context=context, portal=portal)
        try:
            if _should_enter_shell(sys.argv[1:], app):
                run_shell(state)
            else:
                app(obj=state)
        finally:
            portal.call(context.aclose)


def main() -> None:
    context = build_context()
    run(context)


if __name__ == "__main__":
    main()
