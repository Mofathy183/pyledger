"""
Reusable domain validation rules for accounting entities.

These functions support validation of core accounting concepts such as
account references and journal entry balancing. They are intentionally
kept independent of domain models so they can be reused across multiple
workflows and validation layers.
"""

import re


def clean_account_name(value: str) -> str | None:
    """Validate and normalize an account name.

    Account names are used to identify ledger accounts throughout the
    accounting system. To ensure consistent matching and prevent invalid
    references, account names are restricted to alphabetic characters,
    spaces, commas, and forward slashes.

    Leading and trailing whitespace is removed before validation.

    Args:
        value: User-provided account name or abbreviation.

    Returns:
        The normalized account name when validation succeeds,
        otherwise ``None``.

    Notes:
        Numeric characters and unsupported special characters are
        rejected because they do not represent valid account names
        within the current accounting model.
    """
    cleaned = value.strip()
    pattern = r"^[A-Za-z /,]+$"

    if not re.fullmatch(pattern, cleaned):
        return None

    return cleaned


def debits_equal_credits(debit: int, credit: int) -> bool:
    """Determine whether a journal entry is balanced.

    Double-entry accounting requires that total debits equal total
    credits for every journal entry. This invariant must hold before
    a transaction can be accepted into the accounting system.

    Args:
        debit: Total debit amount.
        credit: Total credit amount.

    Returns:
        ``True`` if debits equal credits, otherwise ``False``.
    """
    return debit == credit
