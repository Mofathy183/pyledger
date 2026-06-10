"""
Reusable domain validation rules for accounting entities.

These functions support validation of core accounting concepts such as
account references and journal entry balancing. They are intentionally
kept independent of domain models so they can be reused across multiple
workflows and validation layers.
"""

import re
from decimal import Decimal


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


def is_valid_line_amounts(debit: Decimal, credit: Decimal) -> bool:
    """Validate the posting amounts for a journal line.

    A journal line must represent exactly one side of a double-entry
    accounting transaction. A line may contain either a debit amount or
    a credit amount, but not both.

    Valid examples:

    - Debit = 100, Credit = 0
    - Debit = 0, Credit = 100

    Invalid examples:

    - Debit = 100, Credit = 100
    - Debit = 0, Credit = 0

    Args:
        debit: Debit amount recorded on the journal line.
        credit: Credit amount recorded on the journal line.

    Returns:
        ``True`` if the journal line represents a valid posting,
        otherwise ``False``.
    """
    if debit > 0 and credit > 0:
        return False
    if debit == 0 and credit == 0:
        return False

    return True
