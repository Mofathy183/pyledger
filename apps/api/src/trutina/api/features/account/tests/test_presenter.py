"""Unit tests for the account feature's ViewModel -> Response Schema mapping.

Pure construction only -- no service calls.
"""

import pytest
from trutina.api.features.account.presenter import (
    to_account_response,
    to_chart_of_accounts_response,
    to_delete_account_response,
)
from trutina.api.features.account.schemas import (
    AccountResponse,
    ChartOfAccountsResponse,
    DeleteAccountResponse,
)
from trutina.core.account.dtos import AccountViewModel, ChartOfAccountsViewModel
from trutina.core.account.schemas.account import AccountCategory, NormalBalance


def _make_view_model(
    code: str = "1001",
    name: str = "Cash",
    category: AccountCategory = AccountCategory.ASSET,
    normal_balance: NormalBalance = "debit",
) -> AccountViewModel:
    return AccountViewModel(
        code=code, name=name, category=category, normal_balance=normal_balance
    )


@pytest.mark.unit
class TestToAccountResponse:
    def test_maps_code(self):
        view_model = _make_view_model(code="1001")

        response = to_account_response(view_model)

        assert response.account.code == "1001"

    def test_maps_name(self):
        view_model = _make_view_model(name="Cash")

        response = to_account_response(view_model)

        assert response.account.name == "Cash"

    def test_maps_category(self):
        view_model = _make_view_model(category=AccountCategory.REVENUE)

        response = to_account_response(view_model)

        assert response.account.category is AccountCategory.REVENUE

    def test_maps_normal_balance(self):
        view_model = _make_view_model(normal_balance="credit")

        response = to_account_response(view_model)

        assert response.account.normal_balance == "credit"

    def test_success_is_true(self):
        response = to_account_response(_make_view_model())

        assert response.success is True

    def test_returns_account_response_instance(self):
        response = to_account_response(_make_view_model())

        assert isinstance(response, AccountResponse)


@pytest.mark.unit
class TestToChartOfAccountsResponse:
    def test_maps_empty_accounts(self):
        view_model = ChartOfAccountsViewModel(accounts=[])

        response = to_chart_of_accounts_response(view_model)

        assert response.accounts == []

    def test_maps_single_account(self):
        view_model = ChartOfAccountsViewModel(accounts=[_make_view_model()])

        response = to_chart_of_accounts_response(view_model)

        assert len(response.accounts) == 1
        assert response.accounts[0].code == "1001"

    def test_maps_multiple_accounts_in_order(self):
        view_model = ChartOfAccountsViewModel(
            accounts=[
                _make_view_model(code="1001", name="Cash"),
                _make_view_model(code="2001", name="Revenue"),
            ]
        )

        response = to_chart_of_accounts_response(view_model)

        assert [a.code for a in response.accounts] == ["1001", "2001"]

    def test_returns_chart_of_accounts_response_instance(self):
        response = to_chart_of_accounts_response(ChartOfAccountsViewModel(accounts=[]))

        assert isinstance(response, ChartOfAccountsResponse)


@pytest.mark.unit
class TestToDeleteAccountResponse:
    def test_echoes_deleted_code(self):
        response = to_delete_account_response("1001")

        assert response.code == "1001"

    def test_success_is_true(self):
        response = to_delete_account_response("1001")

        assert response.success is True

    def test_returns_delete_account_response_instance(self):
        response = to_delete_account_response("1001")

        assert isinstance(response, DeleteAccountResponse)
