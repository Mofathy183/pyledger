"""Console-script entry point for the PyLedger CLI.

This is the only place in the application that calls ``asyncio.run()``.
It owns the single event loop for the entire CLI invocation and
guarantees ``CliContext``'s resources are always released -- even if a
command raises, and even on Click's normal ``SystemExit``-based exit
path -- by running the whole Typer dispatch inside
``async with build_context() as context: ...``.

No command body, service, or repository may call ``asyncio.run()``
anywhere else in the codebase. Everything reachable from ``main()`` runs
on the single loop created here.
"""

import asyncio

from pyledger.cli.app import app
from pyledger.cli.bootstrap import build_context


async def _run() -> None:
    """Build one ``CliContext`` for this invocation and guarantee cleanup.

    ``async with build_context() as context`` opens no resources by
    itself -- ``build_context()`` performs no I/O -- but it guarantees
    that ``context.aclose()`` runs when this block exits, whether
    Typer's dispatch (``app(obj=context)``) returns normally, raises an
    application exception, or exits via Click's normal
    ``SystemExit``-based ``--help``/error handling. ``SystemExit`` is a
    regular exception from the interpreter's perspective, so the
    ``async with`` block's cleanup still runs before it propagates out
    of ``_run()``.

    The constructed context is passed to Typer via ``obj=``, so
    ``cli.app.main_callback`` sees an already-populated ``ctx.obj`` and
    does not construct a second, unmanaged ``CliContext`` of its own.
    """
    async with build_context() as context:
        app(obj=context)


def main() -> None:
    """Run the CLI inside a single asyncio event loop.

    Delegates to ``_run()``, the only coroutine this module defines, so
    that ``asyncio.run()`` executes exactly once for the lifetime of the
    process.
    """
    asyncio.run(_run())


if __name__ == "__main__":
    main()
