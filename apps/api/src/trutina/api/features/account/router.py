"""Router for the account feature.

Follows the project's fixed request workflow:

    HTTP Request -> Router -> Request Schema -> Mapper -> Input DTO ->
    Handler -> Service -> ViewModel -> Presenter -> Response Schema ->
    HTTP Response

Each route below does exactly: resolve the Mapper, call the Handler via
``Depends(get_account_service)``, resolve the Presenter, return. No
route contains business logic, constructs a domain model, or catches
``AppError``/``ValidationAppError`` -- those propagate uncaught to
``api/shared/errors/handlers.py``, registered once in
``api/composition/app.py::create_app()``.

Prefixed under ``/accounts``, matching the resource-per-router
convention `Trutina API Feature & Testing Prompt` Section 8 implies
(the ``system`` router is the documented, unprefixed exception -- not a
template to copy here).
"""

from fastapi import APIRouter, Depends, status
from trutina.api.composition.dependencies import get_account_service
from trutina.core.account.service import AccountService

from . import handler
from .mapper import to_create_account_input, to_update_account_input
from .presenter import (
    to_account_response,
    to_chart_of_accounts_response,
    to_delete_account_response,
)
from .schemas import (
    AccountResponse,
    ChartOfAccountsResponse,
    CreateAccountRequest,
    DeleteAccountResponse,
    UpdateAccountRequest,
)

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    request: CreateAccountRequest,
    service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    """Create a new account.

    Raises:
        AppError: DUPLICATE_ACCOUNT_CODE, DUPLICATE_ACCOUNT_NAME
            (translated to 409 by the registered exception handlers).
        ValidationAppError: VALIDATION_ERROR (translated to 422).
    """
    dto = to_create_account_input(request)
    view_model = await handler.create_account(service, dto)
    return to_account_response(view_model)


@router.get("", response_model=ChartOfAccountsResponse)
async def list_accounts(
    service: AccountService = Depends(get_account_service),
) -> ChartOfAccountsResponse:
    """Return every persisted account."""
    view_model = await handler.list_accounts(service)
    return to_chart_of_accounts_response(view_model)


@router.get("/{code}", response_model=AccountResponse)
async def get_account(
    code: str,
    service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    """Fetch a single account by its code.

    Raises:
        AppError: UNKNOWN_ACCOUNT (translated to 404).
    """
    view_model = await handler.get_account(service, code)
    return to_account_response(view_model)


@router.patch("/{code}", response_model=AccountResponse)
async def update_account(
    code: str,
    request: UpdateAccountRequest,
    service: AccountService = Depends(get_account_service),
) -> AccountResponse:
    """Apply a partial update to an existing account.

    Raises:
        AppError: UNKNOWN_ACCOUNT (404), DUPLICATE_ACCOUNT_NAME (409).
        ValidationAppError: VALIDATION_ERROR (422).
    """
    dto = to_update_account_input(code, request)
    view_model = await handler.update_account(service, dto)
    return to_account_response(view_model)


@router.delete("/{code}", response_model=DeleteAccountResponse)
async def delete_account(
    code: str,
    service: AccountService = Depends(get_account_service),
) -> DeleteAccountResponse:
    """Delete an account by its code.

    Raises:
        AppError: UNKNOWN_ACCOUNT (translated to 404).
    """
    await handler.delete_account(service, code)
    return to_delete_account_response(code)
