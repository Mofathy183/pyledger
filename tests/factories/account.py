from pyledger.core.account import CreateAccountInput, UpdateAccountInput
from pyledger.core.account.schemas import Account, AccountCategory, ChartOfAccounts

from tests.fakes import FakeAccountRepo


def make_account(
    code: str = "1001",
    name: str = "Cash",
    category: AccountCategory = AccountCategory.ASSET,
) -> Account:
    return Account(
        code=code,
        name=name,
        category=category,
    )


def make_chart_of_accounts(
    accounts: list[Account] | None = None,
) -> ChartOfAccounts:
    if accounts is None:
        accounts = [
            make_account(),
        ]

    return ChartOfAccounts(accounts=accounts)


def make_create_account_input(
    code: str = "1001",
    name: str = "Cash",
    category: AccountCategory = AccountCategory.ASSET,
) -> CreateAccountInput:
    return CreateAccountInput(
        code=code,
        name=name,
        category=category,
    )


def make_update_account_input(
    code: str = "1001",
    name: str | None = None,
    category: AccountCategory | None = None,
) -> UpdateAccountInput:
    return UpdateAccountInput(
        code=code,
        name=name,
        category=category,
    )


def make_fake_account_repo(
    chart: ChartOfAccounts | None = None,
) -> FakeAccountRepo:
    return FakeAccountRepo(chart=chart)


def make_create_account_request(
    *,
    code: str = "1001",
    name: str = "Cash",
    category: str = AccountCategory.ASSET.value,
) -> dict:
    """Build a POST /accounts request payload.

    Defaults mirror `tests/factories/account.py::make_create_account_input`'s
    defaults, so tests reading both side by side see the same account.
    """
    return {"code": code, "name": name, "category": category}


def make_update_account_request(
    *,
    name: str | None = None,
    category: str | None = None,
) -> dict:
    """Build a PATCH /accounts/{code} request payload.

    Only includes keys that were explicitly provided, mirroring how a
    real HTTP client would omit fields it doesn't want to change --
    `UpdateAccountRequest` treats omitted the same as `None` (see
    `schemas.py`), but building a truly omitted-key payload here (rather
    than always sending `null`) tests the omission path specifically,
    distinct from the explicit-null path.
    """
    payload: dict = {}
    if name is not None:
        payload["name"] = name
    if category is not None:
        payload["category"] = category
    return payload
