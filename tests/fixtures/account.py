import pytest

from pyledger.modules.account.schemas import Account, AccountCategory, ChartOfAccounts
from tests.factories import make_account, make_chart_of_accounts


@pytest.fixture
def account() -> Account:
    return make_account()


@pytest.fixture
def chart_of_accounts() -> ChartOfAccounts:
    return make_chart_of_accounts()


@pytest.fixture
def cash_account() -> Account:
    return make_account(code="1001", name="Cash", category=AccountCategory.ASSET)


@pytest.fixture
def revenue_account() -> Account:
    return make_account(
        code="4001", name="Sales Revenue", category=AccountCategory.REVENUE
    )
