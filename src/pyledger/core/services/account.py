from pyledger.core.models.account import Account


def resolve_account(name: str, accounts: list[Account]) -> Account | None:
    """Resolve an account reference to its registered Account.

    Matches the given name against each account's normalized name
    and aliases. Account references on journal lines and postings
    are already normalized via `clean_account_name`, so comparison
    is a direct equality check.

    Args:
        name: Normalized account name or alias to resolve.
        accounts: The chart of accounts to search.

    Returns:
        The matching Account, or None if no account matches.
    """
    for account in accounts:
        if name == account.name or name in account.aliases:
            return account

    return None
