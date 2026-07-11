"""Mapping helpers for posting API request values.

The posting feature accepts simple path parameters rather than request
bodies because ledger postings are derived from existing journal
entries instead of being created directly by clients.

These helpers normalize and prepare incoming route values before they
cross into the application layer, keeping request transformation
separate from routing logic.
"""


def to_journal_number(journal_number: int) -> int:
    """Map a journal number path parameter to the application layer.

    The value is returned unchanged because no additional transformation
    is required beyond the validation performed by the HTTP layer.

    Args:
        journal_number: The validated journal entry number.

    Returns:
        The journal number passed to the application layer.
    """
    return journal_number


def to_account(account: str) -> str:
    """Normalize an account name supplied in a request path.

    Removes incidental leading and trailing whitespace before the value
    is passed to the application layer. Account normalization and
    canonical lookup remain the responsibility of the domain layer.

    Args:
        account: The account name supplied by the client.

    Returns:
        The normalized account name.
    """
    return account.strip()
