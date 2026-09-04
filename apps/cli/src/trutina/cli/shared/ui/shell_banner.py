"""Welcome banner for the Trutina interactive shell.

Lives in cli/shared/ui/ -- not inside cli/shell/ -- for the same
reason every feature's own presentation lives in its formatter.py
rather than its command.py: shell/loop.py orchestrates the REPL loop,
it doesn't own copywriting, logo art, or layout. Any future consumer
that wants the same "what is Trutina, how do I use it" introduction
can reuse build_welcome_banner() instead of re-authoring it.

Follows the same build/print split as every other formatter in this
package: build_welcome_banner() is pure and returns a renderable;
print_welcome_banner() is the thin, side-effecting wrapper.
"""

from rich.console import Group
from rich.panel import Panel
from rich.text import Text

from .console import console
from .logo import build_logo
from .widgets import panel, rule


def build_welcome_banner() -> Panel:
    """Build the panel shown once, when the interactive shell starts.

    Deliberately compact and single-palette: width is capped so the
    panel doesn't stretch to fill an ultra-wide terminal around a
    handful of characters of content, and every styled element uses
    the brand/brand_dim pair rather than success/info -- this banner
    is identity chrome, not a status message, and shouldn't borrow the
    color vocabulary reserved for real operation outcomes elsewhere in
    the CLI. Content is deliberately minimal: the wordmark+tagline is
    the one identity statement, and `help` is the one pointer into the
    shell's real documentation -- this must never grow into a second,
    driftable copy of what `help` already teaches.

    Returns:
        A configured Rich Panel. Not printed.
    """
    hint = Text.from_markup(
        "[brand_dim]Type[/] [brand]help[/][brand_dim] to get started, "
        "or[/] [brand]exit[/][brand_dim] to leave.[/]"
    )

    body = Group(
        build_logo(),
        Text(""),
        rule(style="brand_dim"),
        hint,
    )

    return panel(body, title="", style="brand")


def print_welcome_banner() -> None:
    """Build and print the interactive shell's welcome banner."""
    console.print(build_welcome_banner())
