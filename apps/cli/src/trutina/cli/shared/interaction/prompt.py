"""
Shared interactive-prompt primitives for the CLI layer.

Extracted from cli/features/account/prompt.py once Journal became the
second interactive feature needing the same primitives — per the
extraction note that module itself left ("not extracted yet — a single
caller does not justify a shared module"). Every interactive prompt
module across CLI features (account, journal, and any future feature)
should build on these functions rather than re-implementing Rich prompt
handling.

Responsibilities:

- Provide themed wrappers around Rich's Prompt/Confirm.
- Render numbered option panels through the shared panel()/rule()
    widgets, consistent with the rest of the CLI's presentation.

Explicitly NOT this module's responsibility:

- Anything feature-specific (account fields, journal lines, etc.).
- DTO construction — callers delegate that to their own parser module.
"""

from collections.abc import Callable

from rich.console import Group
from rich.prompt import Confirm, Prompt
from rich.text import Text
from trutina.cli.shared.ui import console, panel, rule


def ask(message: str, *, default: str | None = None, style: str = "info") -> str:
    """Themed wrapper around Prompt.ask() for consistent CLI prompting.

    Args:
        message: The prompt label shown to the user, wrapped in the
            given theme ``style`` before rendering.
        default: Value reused if the user presses Enter without typing
            anything. Omitted (None) when there is no sensible default.
        style: A theme style name registered on the shared console.
            Defaults to "info".

    Returns:
        The value entered by the user, or ``default`` if left blank.
    """
    prompt_text = f"[{style}]{message}[/]"
    if default is not None:
        return Prompt.ask(prompt_text, default=default, console=console)
    return Prompt.ask(prompt_text, console=console)


def confirm(message: str, *, default: bool = False, style: str = "warning") -> bool:
    """Themed wrapper around Confirm.ask() returning a plain boolean.

    Args:
        message: The confirmation prompt shown to the user, wrapped in
            the given theme ``style`` before rendering.
        default: The value used if the user presses Enter without
            typing anything.
        style: A theme style name registered on the shared console.
            Defaults to "warning"; callers confirming a destructive
            action should pass "error" instead.

    Returns:
        True if the user confirms; otherwise False.
    """
    prompt_text = f"[{style}]{message}[/]"
    return Confirm.ask(prompt_text, default=default, console=console)


def select[T](
    message: str,
    options: list[T],
    *,
    default: T | None = None,
    label: Callable[[T], str] = str,
    style: str = "info",
    title: str = "Select an Option",
) -> T:
    """Present a numbered list of options in a panel and return the choice.

    Args:
        message: Heading shown at the top of the panel.
        options: The selectable values, displayed in list order.
        default: Preselected option used if the user presses Enter
            without typing a number. Must be a member of ``options`` if
            provided.
        label: Callable mapping an option to its display string.
        style: A theme style name applied to the heading, rule, and
            option numbers.
        title: Panel title shown in the border.

    Returns:
        The selected option value — not the number the user typed.
    """
    option_lines = []
    for index, option in enumerate[T](options, start=1):
        suffix = (
            " [dim](default)[/]" if default is not None and option == default else ""
        )
        option_lines.append(
            Text.from_markup(f"  [{style}]{index}.[/] {label(option)}{suffix}")
        )

    content = Group(
        Text(message, style=style),
        rule(style=style),
        *option_lines,
    )
    console.print(panel(content, title=title, style=style))

    choices = [str(i) for i in range(1, len(options) + 1)]

    if default is not None:
        choice = Prompt.ask(
            f"[{style}]Enter a number[/]",
            choices=choices,
            default=str(options.index(default) + 1),
            show_choices=False,
            console=console,
        )
    else:
        choice = Prompt.ask(
            f"[{style}]Enter a number[/]",
            choices=choices,
            show_choices=False,
            console=console,
        )

    return options[int(choice) - 1]
