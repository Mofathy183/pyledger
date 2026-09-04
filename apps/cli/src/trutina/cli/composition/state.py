"""Bridges the synchronous Click/Typer world to the single async event loop.

AppState is what gets threaded through Typer via ``ctx.obj``. It pairs a
CliContext (async accessors) with the BlockingPortal that makes those
accessors callable from a plain, synchronous command function.
"""

from dataclasses import dataclass
from typing import TypeVar

from anyio.from_thread import BlockingPortal

from .context import CliContext

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class CliState:
    """Carries the CliContext and the portal used to call into its event loop.

    Command functions are plain ``def`` — never ``async def``. Any command
    that needs an async accessor (``get_account_service()``, etc.) defines a
    small local coroutine and runs it via ``state.call(...)``.
    """

    context: CliContext
    portal: BlockingPortal

    def call(self, func, *args: object):
        """Run an async callable to completion on the CLI's single event loop.

        Blocks the calling (main) thread until ``func(*args)`` resolves.
        This is the only sanctioned way for a command body to reach an
        async ``CliContext``/service/repository accessor.
        """
        return self.portal.call(func, *args)
