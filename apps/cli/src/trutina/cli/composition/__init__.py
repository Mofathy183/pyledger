"""Composition-root package for the Trutina CLI.

Groups the four modules that build and wire the CLI's dependency
graph -- the Typer app itself, the composition root that builds a
CliContext, the per-invocation dependency container, and the
sync-to-async bridge threaded through Typer via ctx.obj -- so they
sit together instead of loose at the top of cli/, alongside the
shell/ and shared/ui/ groupings already established.

Every symbol here is also still importable from its original
top-level path (trutina.cli.app, trutina.cli.bootstrap,
trutina.cli.context, trutina.cli.state) -- those modules now forward
to this package rather than defining anything themselves, so no
existing import anywhere in the codebase (tests included) needed to
change for this move.
"""

from .app import app, main_callback
from .bootstrap import build_context
from .context import CliContext
from .state import CliState

__all__ = ["app", "main_callback", "build_context", "CliContext", "CliState"]
