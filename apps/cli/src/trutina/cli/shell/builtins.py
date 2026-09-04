"""Shell built-in keywords for the Trutina interactive shell.

Kept as a single source of truth, separate from both loop.py (which
reads it to decide how each built-in keyword should be handled) and
completion.py (which surfaces it in the completion menu) -- so the
two can never silently drift out of agreement.

Each builtin carries both its user-facing description (shown in the
completion menu, exactly like a real command's --help text) and
whether typing it ends the session. This is deliberately one dict,
not two -- a separate hand-maintained "which keywords terminate the
loop" set alongside this one would reintroduce exactly the kind of
drift risk bugfix #6 already fixed once for description text alone,
just for a different fact about each builtin instead.

These are shell-loop concepts, not Typer commands -- they have no
corresponding function in app.py's command tree, which is exactly why
they need to be added here rather than discovered from the Click app
the way every other completion entry is.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ShellBuiltin:
    """A single shell-only keyword: its help text and its effect on the loop."""

    description: str
    terminates: bool = False


SHELL_BUILTINS: dict[str, ShellBuiltin] = {
    "exit": ShellBuiltin(
        description="Leave the interactive shell.",
        terminates=True,
    ),
    "help": ShellBuiltin(
        description="Show available commands, or help for one command.",
    ),
}


def terminating_keywords() -> frozenset[str]:
    """Return the SHELL_BUILTINS keys that end the loop when typed.

    The single derivation point for "which keywords exit the shell" --
    loop.py reads this instead of re-deriving its own frozenset
    locally, so the loop and this catalog can never drift apart the
    way a hand-maintained ("exit", "quit") tuple could.
    """
    return frozenset(
        name for name, builtin in SHELL_BUILTINS.items() if builtin.terminates
    )
