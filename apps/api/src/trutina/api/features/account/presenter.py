"""ViewModel -> Response Schema mapping for the account feature.

Pure, synchronous, no I/O, no business rules -- mirrors ``mapper.py``'s
role on the output side. Each function turns an already-fetched
``AccountViewModel``/``ChartOfAccountsViewModel`` into its public HTTP
response shape; it never calls a service.
"""

from trutina.core.account.dtos import AccountViewModel, ChartOfAccountsViewModel

from .schemas import (
    AccountData,
    AccountResponse,
    ChartOfAccountsResponse,
    DeleteAccountResponse,
)


def _to_account_data(view_model: AccountViewModel) -> AccountData:
    """Map a single AccountViewModel to its wire-level AccountData shape."""
    return AccountData(
        code=view_model.code,
        name=view_model.name,
        category=view_model.category,
        normal_balance=view_model.normal_balance,
    )


def to_account_response(view_model: AccountViewModel) -> AccountResponse:
    """Build the response envelope for a single-account result.

    Used by create, get, and update -- all three return one
    ``AccountViewModel`` from the service.

    Args:
        view_model: The service's view model for one account.

    Returns:
        The response body for ``POST /accounts``, ``GET
        /accounts/{code}``, and ``PATCH /accounts/{code}``.
    """
    return AccountResponse(account=_to_account_data(view_model))


def to_chart_of_accounts_response(
    view_model: ChartOfAccountsViewModel,
) -> ChartOfAccountsResponse:
    """Build the response envelope for the full chart-of-accounts listing.

    Args:
        view_model: The service's chart-of-accounts view model.

    Returns:
        The response body for ``GET /accounts``.
    """
    return ChartOfAccountsResponse(
        accounts=[_to_account_data(account) for account in view_model.accounts]
    )


def to_delete_account_response(code: str) -> DeleteAccountResponse:
    """Build the response envelope confirming a successful deletion.

    Args:
        code: The account code that was deleted.

    Returns:
        The response body for ``DELETE /accounts/{code}``.
    """
    return DeleteAccountResponse(code=code)
