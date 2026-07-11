"""Request Schema -> Input DTO mapping for the account feature.

Pure, synchronous, no I/O, no business rules -- per
`PyLedger API Feature & Testing Prompt` Section 2/3. Each function here
does field-for-field construction only; every mapper below is a thin
`InputDTO(**request.model_dump())`-equivalent because
`CreateAccountRequest`/`UpdateAccountRequest` were deliberately built to
mirror `CreateAccountInput`/`UpdateAccountInput` field-for-field (see
`schemas.py`). Domain/business validation is not this module's job --
it fires when the handler calls into `AccountService`.
"""

from pyledger.modules.account.dtos import CreateAccountInput, UpdateAccountInput

from .schemas import CreateAccountRequest, UpdateAccountRequest


def to_create_account_input(request: CreateAccountRequest) -> CreateAccountInput:
    """Map a create request body to the service's Input DTO.

    Args:
        request: The validated ``POST /accounts`` request body.

    Returns:
        The ``CreateAccountInput`` ready to pass into
        ``AccountService.create_account()``.
    """
    return CreateAccountInput(
        code=request.code,
        name=request.name,
        category=request.category,
    )


def to_update_account_input(
    code: str, request: UpdateAccountRequest
) -> UpdateAccountInput:
    """Map an update request body plus its path-supplied code to the Input DTO.

    ``code`` arrives from the URL path (``PATCH /accounts/{code}``), not
    the request body -- see ``UpdateAccountRequest``'s docstring for why
    the body itself carries no code field.

    Args:
        code: The account code from the URL path, identifying which
            account to update.
        request: The validated ``PATCH /accounts/{code}`` request body.

    Returns:
        The ``UpdateAccountInput`` ready to pass into
        ``AccountService.update_account()``.
    """
    return UpdateAccountInput(
        code=code,
        name=request.name,
        category=request.category,
    )
