from pyledger.modules.account import CreateAccountInput, UpdateAccountInput
from pyledger.modules.account.schemas import Account, AccountCategory, ChartOfAccounts
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
