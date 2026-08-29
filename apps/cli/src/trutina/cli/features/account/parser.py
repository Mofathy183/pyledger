"""
CLI-argument-to-DTO adapter for the Account CLI feature.

``parser.py`` is the input adapter for command-line arguments, mirroring
the interactive path in ``prompts.py``. Both adapters funnel into these
same two functions, so DTO construction has a single source of truth
regardless of whether values came from Typer options or Rich prompts:

    Typer arguments -----> parse_*() -----> DTO
    Rich prompts (prompts.py) -----> parse_*() -----> DTO

Responsibilities:

- Accept raw values (strings, or None for omitted update fields).
- Construct and return the corresponding application DTO
    (CreateAccountInput / UpdateAccountInput).
- Normalize incidental input noise (surrounding whitespace) that is not
    itself a validation concern.
- Resolve a raw, case-insensitive category string (e.g. "asset",
    "Asset", "ASSET") into the corresponding AccountCategory member.
    This is the single place category resolution happens — both the
    CLI-flag path and the interactive path (prompts.py) always supply
    a raw string here, never an AccountCategory instance.

Explicitly NOT this module's responsibility:

- Business or domain validation. Field-level and cross-field validation
    is owned entirely by the DTOs (structural) and the domain Account
    model (business rules), both of which raise through the existing
    pydantic.ValidationError -> ValidationAppError path. This module
    never pre-validates or swallows those errors.
- Calling services or repositories.
- Rich prompting, rendering, or console output.
- Deciding whether a field was "changed" — for updates, that decision
    belongs to the caller (interactive: always supplies a value; CLI
    flags: omits a flag to leave a field unset via None).

This module must never be imported by service or domain code — the
dependency direction is CLI -> parser -> DTO, never the reverse.
"""

import typer
from trutina.core.account import CreateAccountInput, UpdateAccountInput
from trutina.core.account.schemas.account import AccountCategory


def _clean(value: str) -> str:
    """Strip incidental surrounding whitespace from raw CLI input.

    This is normalization of input noise (e.g. a trailing space from a
    copy-pasted terminal argument), not domain validation. Genuine
    validation failures still surface from the DTO/domain layers
    unchanged — this only prevents whitespace alone from causing an
    otherwise-valid value to fail downstream.

    Args:
        value: Raw string value from a Typer argument or Rich prompt.

    Returns:
        The value with leading/trailing whitespace removed.
    """
    return value.strip()


def _get_category(category: str) -> AccountCategory:
    """Resolve a raw, case-insensitive category string to its enum member.

    Accepts any casing (``"asset"``, ``"Asset"``, ``"ASSET"``) so users
    are never forced to match the enum's stored casing exactly. This is
    the only place in the Account CLI feature that performs this
    resolution — both ``parse_create_account`` and
    ``parse_update_account`` delegate here rather than duplicating the
    lookup.

    Args:
        category: Raw category string, in any casing.

    Returns:
        The matching AccountCategory member.

    Raises:
        typer.BadParameter: If ``category`` does not match any
            AccountCategory member name, case-insensitively.
    """
    normalized = category.strip().upper()

    try:
        resolved_category = AccountCategory[normalized]
    except KeyError:
        valid = ", ".join(c.name.title() for c in AccountCategory)
        raise typer.BadParameter(
            f"'{category}' is not a valid category. Choose from: {valid}."
        ) from None

    return resolved_category


def parse_create_account(
    *,
    code: str,
    name: str,
    category: str,
) -> CreateAccountInput:
    """Build a CreateAccountInput from raw create-flow values.

    ``category`` is always a raw string here — both the CLI-flag path
    (a Typer option value) and the interactive path (``prompts.py``)
    converge on plain strings before reaching this function, so
    ``_get_category()`` is the single place category resolution happens
    regardless of input source. Matching on name is case-insensitive
    (``"asset"``, ``"Asset"``, and ``"ASSET"`` all resolve the same way);
    an unrecognized value raises ``typer.BadParameter`` rather than
    reaching Pydantic.

    Args:
        code: Raw account code, as typed or prompted.
        name: Raw account name, as typed or prompted.
        category: Raw category string, as typed or prompted (e.g.
            ``"asset"``).

    Returns:
        The constructed CreateAccountInput.

    Raises:
        typer.BadParameter: If ``category`` does not match any
            AccountCategory member name, case-insensitively.
        pydantic.ValidationError: If ``code`` or ``name`` fails
            CreateAccountInput's structural validation.
    """
    return CreateAccountInput(
        code=_clean(code),
        name=_clean(name),
        category=_get_category(category),
    )


def parse_update_account(
    *,
    code: str,
    name: str | None = None,
    category: str | None = None,
) -> UpdateAccountInput:
    """Build an UpdateAccountInput from raw update-flow values.

    ``code`` identifies the account being updated and is never itself
    changed — it is not re-prompted or re-parsed as a new value.
    ``name``/``category`` follow UpdateAccountInput's own omitted-field
    semantics: passing None here means "leave this field unchanged," not
    "clear this field." The interactive prompts path always supplies
    concrete values (pre-filled with the account's current value as the
    prompt default); the CLI-flag path supplies None for any flag the
    caller did not pass.

    ``category``, when provided, is always a raw string (e.g.
    ``"revenue"``) resolved case-insensitively via ``_get_category()`` —
    identical to ``parse_create_account``. When ``category`` is None,
    it is passed through as None rather than resolved, since an empty
    or missing value here means "unchanged," not "invalid."

    Args:
        code: The account code identifying which account to update.
        name: New name, or None to leave the current name unchanged.
        category: New category as a raw string, or None to leave the
            current category unchanged.

    Returns:
        The constructed UpdateAccountInput.

    Raises:
        typer.BadParameter: If ``category`` is provided but does not
            match any AccountCategory member name, case-insensitively.
        pydantic.ValidationError: If a provided field fails
            UpdateAccountInput's structural validation.
    """
    return UpdateAccountInput(
        code=_clean(code),
        name=_clean(name) if name is not None else None,
        category=_get_category(category) if category is not None else None,
    )
