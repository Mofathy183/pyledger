"""
Interactive input adapter for the Account CLI feature.

``prompt.py`` is the interactive input adapter for Account commands. It
collects account-specific values through the shared
``cli.shared.interaction`` primitives and delegates DTO construction to
``parser.py``. It is the interactive counterpart to CLI argument
parsing—both input paths funnel through the same parser functions so
application DTOs have a single source of truth regardless of how the
input was collected.

    User -> Shared Interaction -> Python values -> parser.py -> DTO

Responsibilities:

- Collect feature-specific interactive input.
- Delegate generic prompt rendering to ``cli.shared.interaction``.
- Delegate DTO construction to ``parser.py``.
- Present account-specific choices (such as account categories) while
    preserving the same raw input shape expected by the CLI-flag path.

Explicitly NOT this module's responsibility:

- Calling services or repositories.
- Checking account existence or uniqueness.
- Business or domain validation, including category resolution—
    ``_prompt_category()`` returns the raw selected string; resolving
    it to an ``AccountCategory`` member is ``parser.py``'s job via
    ``_get_category()``, identical to the CLI-flag path.
- Rendering command result output (create/update/get), which belongs
    to ``formatter.py``.
- Implementing generic prompting behavior such as text input,
    confirmation prompts, or option selection—these responsibilities
    belong to ``cli.shared.interaction``.
- Catching service exceptions.

This module adapts interactive user input into the parser layer. It
must never construct application DTOs directly (for example,
``CreateAccountInput(...)``) or perform domain validation itself.
"""

from trutina.cli.shared.interaction import ask, confirm, select
from trutina.core.account.dtos import CreateAccountInput, UpdateAccountInput
from trutina.core.account.schemas.account import AccountCategory

from .parser import (
    parse_create_account,
    parse_update_account,
)

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
    return ask("Account Code")


def _prompt_name(default: str | None = None) -> str:
    """Prompt for the account name.

    Args:
        default: Existing name to reuse if the user presses Enter.
            Omitted for creation flows.

    Returns:
        The account name as entered by the user.
    """
    return ask("Account Name", default=default)


def _prompt_category(default: AccountCategory | None = None) -> str:
    """Prompt for the account category using the shared selection helper.

    Presents the available ``AccountCategory`` members through the shared
    interaction layer but returns the selected value as a raw string
    (the member's ``.value``, for example ``"asset"``) rather than an
    ``AccountCategory`` instance. This preserves the same input shape as
    the CLI-flag path so both workflows delegate category resolution to
    ``parser.py``'s ``_get_category()``.

    Args:
        default: Existing category to preselect if the user presses
            Enter without choosing a different option. Omitted for
            creation flows.

    Returns:
        The selected category as a raw string.
    """
    options = [category.value for category in AccountCategory]
    default_value = default.value if default is not None else None

    return select(
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

    Collects an account identifier for later resolution by the parser
    or service layer. No lookup, validation, or account resolution is
    performed here.

    Returns:
        The account identifier (code) exactly as entered by the
        user.
    """
    return ask("Account identifier Code")


def confirm_account_deletion(name: str) -> bool:
    """Request confirmation before deleting an account.

    Uses the shared interaction layer's ``"error"`` presentation style
    to emphasize that account deletion is a destructive operation.

    Args:
        name: Display name of the account shown in the confirmation
            prompt.

    Returns:
        True if the user confirms deletion; otherwise False.
    """
    return confirm(f'Delete account "{name}"?', default=False, style="error")
