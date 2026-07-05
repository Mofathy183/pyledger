"""
Interactive prompt adapter for the Account CLI feature.

``prompts.py`` is an interactive input adapter, not a business-logic
module: it collects values through Rich prompts and hands them to
``parser.py`` to become application DTOs. It is the interactive
counterpart to CLI argument parsing — both paths funnel through the
same parser functions, so DTO construction has a single source of
truth regardless of how the input was collected.

    User -> Rich Prompt -> Python values -> parser.py -> DTO

Responsibilities:

- Collect interactive user input.
- Provide user-friendly prompt messages and defaults.
- Present selectable options (e.g. account categories) inside the same
    panel/rule presentation used by the rest of the CLI, and return
    the selection as a raw string, matching the CLI-flag path's input
    shape exactly.
- Delegate DTO construction to ``parser.py``.
- Render every prompt through the shared themed console (``cli.shared.ui``)
    rather than Rich's own default console, so prompts use the same
    ``info``/``warning``/``error`` style vocabulary as the rest of the
    CLI (panels, tables, journal/account output). This is why every
    ``Prompt.ask()``/``Confirm.ask()`` call below passes
    ``console=console`` explicitly — without it, style markup like
    ``[info]...[/]`` would raise, since Rich's default console has no
    knowledge of PyLedger's custom theme names.

Explicitly NOT this module's responsibility:

- Calling services or repositories.
- Checking account existence or uniqueness.
- Business or domain validation, including category resolution —
    ``_prompt_category()`` returns the raw selected string; resolving
    it to an ``AccountCategory`` member is ``parser.py``'s job via
    ``_get_category()``, identical to the CLI-flag path.
- Rendering result panels for command output (create/update/get) — those
    live in ``formatter.py``. The panel here is presentation for the
    *question*, not the answer.
- Catching service exceptions.

This module must never construct application DTOs directly (e.g.
``CreateAccountInput(...)``). All DTO construction is delegated to the
imported parser functions.

Scalability note: ``_ask()``, ``_confirm()``, and ``_select()`` contain
no account-specific behavior and are candidates for extraction into a
shared ``cli`` interaction module once a second interactive feature
(Journal, Posting, Reports) needs the same primitives. Not extracted
yet — a single caller does not justify a shared module.
"""

from collections.abc import Callable

from rich.console import Group
from rich.prompt import Confirm, Prompt
from rich.text import Text

from pyledger.cli.shared.ui import console, panel, rule
from pyledger.modules.account.dtos import CreateAccountInput, UpdateAccountInput
from pyledger.modules.account.schemas.account import AccountCategory

from .parser import (
    parse_create_account,
    parse_update_account,
)

# ---------------------------------------------------------------------------
# Generic Interaction Helpers
# ---------------------------------------------------------------------------


def _ask(message: str, *, default: str | None = None, style: str = "info") -> str:
    """Small wrapper around ``Prompt.ask()`` for consistent CLI prompting.

    Centralizes prompt styling, default handling, and console selection
    so every field prompt in this module behaves and looks consistent.
    Purely an interaction helper — it has no knowledge of services or
    DTOs.

    Args:
        message: The prompt label shown to the user, wrapped in the
            given theme ``style`` before rendering.
        default: Value reused if the user presses Enter without typing
            anything. Omitted (None) when there is no sensible default.
        style: A theme style name registered on the shared console
            (e.g. ``"info"``, ``"warning"``, ``"error"``). Defaults to
            ``"info"``, matching the label style used elsewhere in the
            CLI for ordinary informational prompts.

    Returns:
        The value entered by the user, or ``default`` if left blank.
    """
    prompt_text = f"[{style}]{message}[/]"
    if default is not None:
        return Prompt.ask(prompt_text, default=default, console=console)
    return Prompt.ask(prompt_text, console=console)


def _confirm(message: str, *, default: bool = False, style: str = "warning") -> bool:
    """Wrapper around ``Confirm.ask()`` returning a plain boolean.

    Args:
        message: The confirmation prompt shown to the user, wrapped in
            the given theme ``style`` before rendering.
        default: The value used if the user presses Enter without
            typing anything.
        style: A theme style name registered on the shared console.
            Defaults to ``"warning"``; callers confirming a destructive
            action (e.g. deletion) should pass ``"error"`` instead.

    Returns:
        True if the user confirms; otherwise False.
    """
    prompt_text = f"[{style}]{message}[/]"
    return Confirm.ask(prompt_text, default=default, console=console)


def _select[T](
    message: str,
    options: list[T],
    *,
    default: T | None = None,
    label: Callable[[T], str] = str,
    style: str = "info",
    title: str = "Select an Option",
) -> T:
    """Present a numbered list of options in a panel and return the choice.

    Renders through the same ``panel()``/``rule()`` building blocks used
    for command output elsewhere in the CLI (e.g. ``print_account``),
    rather than as bare printed lines, so a multi-line question reads
    consistently with the rest of the app. The trailing number prompt
    hides Rich's default ``[1/2/3/...]`` choices echo — it would only
    repeat what the panel above already shows.

    Generic and reusable by any future CLI feature that needs to offer
    a fixed set of choices (e.g. journal line types, report formats)
    without asking users to type raw enum names.

    Args:
        message: Heading shown at the top of the panel.
        options: The selectable values, displayed in list order.
        default: Preselected option used if the user presses Enter
            without typing a number. Marked "(default)" next to its
            entry in the panel. Omitted (None) when a choice must be
            made explicitly. Must be a member of ``options`` if
            provided.
        label: Callable mapping an option to its display string. Defaults
            to ``str``.
        style: A theme style name applied to the heading, rule, and
            option numbers. Defaults to ``"info"``.
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

    # Prompt.ask()'s return type is `str` when `default` is omitted, but
    # widens to `str | DefaultType` when `default=` is passed explicitly
    # (even `default=None`). Branching here — rather than always passing
    # `default=default_index` where `default_index: str | None` — keeps
    # `choice` typed as plain `str` in both branches, so `int(choice)`
    # below type-checks without a spurious `None` case.
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


# ---------------------------------------------------------------------------
# Field Prompt Helpers
# ---------------------------------------------------------------------------


def _prompt_code() -> str:
    """Prompt for the account code.

    Only used by the create flow — account codes are immutable, so the
    update flow never re-prompts for one.

    Returns:
        The account code as entered by the user.
    """
    return _ask("Account Code")


def _prompt_name(default: str | None = None) -> str:
    """Prompt for the account name.

    Args:
        default: Existing name to reuse if the user presses Enter.
            Omitted for creation flows.

    Returns:
        The account name as entered by the user.
    """
    return _ask("Account Name", default=default)


def _prompt_category(default: AccountCategory | None = None) -> str:
    """Prompt for the account category via a panel-rendered selection.

    Presents AccountCategory members as a numbered list but returns the
    selection as a raw string (the member's ``.value``, e.g.
    ``"asset"``) rather than an ``AccountCategory`` instance. This
    matches the shape of the CLI-flag path exactly, so both funnel into
    ``parser.py``'s ``_get_category()`` for resolution — the interactive
    path must never hand parser.py an already-resolved enum member.

    Args:
        default: Existing category to preselect if the user presses
            Enter without choosing a number. Omitted for creation flows.

    Returns:
        The selected category as a raw string.
    """
    options = [category.value for category in AccountCategory]
    default_value = default.value if default is not None else None

    return _select(
        "Choose account category",
        options,
        default=default_value,
        label=lambda value: value.title(),
        title="Account Category",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def prompt_create_account() -> CreateAccountInput:
    """Interactively collect the fields required to create an account.

    Prompts for the account code, name, and category, then delegates
    DTO construction to ``parse_create_account()``. This function
    never constructs ``CreateAccountInput`` directly.

    Returns:
        The ``CreateAccountInput`` DTO built by the parser from the
        collected values.
    """
    code = _prompt_code()
    name = _prompt_name()
    category = _prompt_category()

    return parse_create_account(
        code=code,
        name=name,
        category=category,
    )


def prompt_update_account(
    *,
    current_code: str,
    current_name: str,
    current_category: AccountCategory,
) -> UpdateAccountInput:
    """Interactively collect the fields required to update an account.

    Each field prompt is seeded with the account's current value as its
    default, so pressing Enter reuses the existing value. This lets the
    same prompt shape serve both "change this field" and "leave this
    field alone" without separate create/update prompt logic.

    ``current_category`` is accepted as an ``AccountCategory`` (the
    natural shape coming from the account's ViewModel) purely to seed
    the prompt's default selection — ``_prompt_category()`` converts it
    to a raw string internally before it ever reaches ``parser.py``.

    Args:
        current_code: The existing account code. Used only as the
            identifier passed to the parser — code is immutable and is
            not re-prompted.
        current_name: The account's current name, used as the prompt
            default.
        current_category: The account's current category, used as the
            prompt default.

    Returns:
        The ``UpdateAccountInput`` DTO built by the parser from the
        collected values.
    """
    name = _prompt_name(default=current_name)
    category = _prompt_category(default=current_category)

    return parse_update_account(
        code=current_code,
        name=name,
        category=category,
    )


def prompt_account_identifier() -> str:
    """Prompt the user for an account identifier.

    Returns the raw identifier string as typed, with no resolution or
    lookup performed.

    Returns:
        The account identifier (code or name) as entered by the user.
    """
    return _ask("Account identifier")


def confirm_account_deletion(name: str) -> bool:
    """Ask the user to confirm deletion of an account.

    Uses the ``"error"`` theme style rather than the default
    ``"warning"`` — deletion is destructive and irreversible, and
    should read as more severe than an ordinary confirmation.

    Args:
        name: Display name of the account to be deleted, shown in the
            confirmation prompt.

    Returns:
        True if the user confirms deletion; otherwise False.
    """
    return _confirm(f'Delete account "{name}"?', default=False, style="error")
