"""Console-script entry point for the Trutina CLI.

This is the only place in the application that opens the CLI's single
event loop, via ``start_blocking_portal()``. No command, service, or
repository may create a second loop -- there is exactly one, for the
life of the process.
"""

from anyio.from_thread import start_blocking_portal
from trutina.cli.app import app
from trutina.cli.bootstrap import build_context
from trutina.cli.context import CliContext
from trutina.cli.state import CliState


def run(context: CliContext, *, backend: str = "asyncio") -> None:
    """Dispatch the Typer app against one ``CliContext`` and guarantee cleanup.

    Opens the CLI's single event loop on a background thread via
    ``start_blocking_portal()`` and runs the full, synchronous Typer
    dispatch (``app(obj=state)``) on the calling (main) thread.
    ``CliState.call()`` is the only bridge a command may use to reach
    ``context``'s async accessors.

    ``context.aclose()`` is guaranteed to run when this function returns
    -- whether ``app(obj=state)`` returns normally, raises an application
    exception, or exits via Click's normal ``SystemExit``-based
    ``--help``/error handling.

    Split out from ``main()`` so it can be exercised in tests against a
    ``CliContext`` backed by fake repositories, without touching real
    settings or MongoDB.

    Args:
        context: The ``CliContext`` for this invocation. Caller-owned;
            this function does not construct one.
        backend: The anyio backend to run the event loop on. Defaults to
            ``"asyncio"``; tests may pass ``"trio"`` if ever needed.
    """
    with start_blocking_portal(backend=backend) as portal:
        state = CliState(context=context, portal=portal)
        try:
            app(obj=state)
        finally:
            # aclose() is async -- must run on the portal's loop, same
            # as every other CliContext accessor.
            portal.call(context.aclose)


def main() -> None:
    """Build the production ``CliContext`` and run the CLI.

    The only function in the codebase that calls ``build_context()``
    with no explicit ``Settings`` -- meaning this is the only call site
    that resolves real, environment-sourced configuration.
    """
    context = build_context()
    run(context)


if __name__ == "__main__":
    main()
