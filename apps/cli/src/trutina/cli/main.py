"""Console-script entry point for the Trutina CLI.

This is the only place in the application that opens the CLI's single
event loop, via ``start_blocking_portal()``. No command, service, or
repository may create a second loop -- there is exactly one, for the
life of the process.
"""
import sys

from anyio.from_thread import start_blocking_portal
from trutina.cli.app import app
from trutina.cli.bootstrap import build_context
from trutina.cli.context import CliContext
from trutina.cli.shell import run_shell
from trutina.cli.state import CliState


def _known_commands(typer_app) -> set[str]:
    """Return the top-level command/group names Typer will dispatch directly.

    Derived from ``typer_app.registered_groups`` so a new feature (a
    future ``reporting`` group, say) is picked up automatically --
    nothing here needs to change when app.py registers a new group.
    """
    return {group.name for group in typer_app.registered_groups if group.name}


def _should_enter_shell(argv: list[str], typer_app) -> bool:
    """Decide whether argv should drop into the shell or dispatch normally.

    Per the interactive-shell plan (D1): a bare invocation, or a first
    token that isn't a registered command/group name -- including
    ``--help`` -- enters the shell. Only a recognized command name
    triggers Typer's normal one-shot dispatch, so e.g.
    ``account --help`` still dispatches normally and Typer handles its
    own help text unaffected.
    """
    if not argv:
        return True
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


# def run(context: CliContext, *, backend: str = "asyncio") -> None:
#     """Dispatch the Typer app against one ``CliContext`` and guarantee cleanup.

#     Opens the CLI's single event loop on a background thread via
#     ``start_blocking_portal()`` and runs the full, synchronous Typer
#     dispatch (``app(obj=state)``) on the calling (main) thread.
#     ``CliState.call()`` is the only bridge a command may use to reach
#     ``context``'s async accessors.

#     ``context.aclose()`` is guaranteed to run when this function returns
#     -- whether ``app(obj=state)`` returns normally, raises an application
#     exception, or exits via Click's normal ``SystemExit``-based
#     ``--help``/error handling.

#     Split out from ``main()`` so it can be exercised in tests against a
#     ``CliContext`` backed by fake repositories, without touching real
#     settings or MongoDB.

#     Args:
#         context: The ``CliContext`` for this invocation. Caller-owned;
#             this function does not construct one.
#         backend: The anyio backend to run the event loop on. Defaults to
#             ``"asyncio"``; tests may pass ``"trio"`` if ever needed.
#     """
#     with start_blocking_portal(backend=backend) as portal:
#         state = CliState(context=context, portal=portal)
#         try:
#             app(obj=state)
#         finally:
#             # aclose() is async -- must run on the portal's loop, same
#             # as every other CliContext accessor.
#             portal.call(context.aclose)


# def main() -> None:
#     """Build the production ``CliContext`` and run the CLI.

#     The only function in the codebase that calls ``build_context()``
#     with no explicit ``Settings`` -- meaning this is the only call site
#     that resolves real, environment-sourced configuration.
#     """
#     context = build_context()
#     run(context)


if __name__ == "__main__":
    main()
