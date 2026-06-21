import pytest

from pyledger.modules.account.schemas.account import Account
from pyledger.modules.account.schemas.chart import ChartOfAccounts
from tests.factories import make_account, make_chart_of_accounts


@pytest.fixture
def account() -> Account:
    return make_account()


@pytest.fixture
def chart_of_accounts() -> ChartOfAccounts:
    return make_chart_of_accounts()
