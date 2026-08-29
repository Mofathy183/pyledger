import pytest
from pydantic import ValidationError
from trutina.shared.errors import ErrorCode

from tests.factories import make_account, make_chart_of_accounts


@pytest.mark.unit
class TestChartOfAccounts:
    def test_creates_with_unique_accounts(self, account):
        accounts = [
            account,
            make_account(
                code="4001",
                name="Sales Revenue",
            ),
        ]

        chart = make_chart_of_accounts(accounts=accounts)

        assert len(chart.accounts) == 2

    @pytest.mark.parametrize(
        "name",
        [
            "cash",
            "CASH",
            "cAsH",
        ],
    )
    def test_returns_account_when_name_exists_case_insensitively(
        self,
        name,
        account,
    ):
        chart = make_chart_of_accounts(accounts=[account])

        result = chart.get_by_name(name)

        assert result is account

    def test_returns_none_when_name_does_not_exist(self):
        chart = make_chart_of_accounts()

        result = chart.get_by_name("Equipment")

        assert result is None

    def test_returns_account_when_code_exists(self, account):
        chart = make_chart_of_accounts(accounts=[account])

        result = chart.get_by_code("1001")

        assert result is account

    def test_returns_none_when_code_does_not_exist(self):
        chart = make_chart_of_accounts()

        result = chart.get_by_code("9999")

        assert result is None

    def test_raises_validation_error_when_account_code_is_duplicated(
        self,
        account,
    ):
        accounts = [
            account,
            make_account(
                code="1001",
                name="Petty Cash",
            ),
        ]

        with pytest.raises(ValidationError) as exc_info:
            make_chart_of_accounts(accounts=accounts)

        errors = exc_info.value.errors()

        assert any(
            error["type"] == ErrorCode.DUPLICATE_ACCOUNT_CODE for error in errors
        )

    def test_raises_validation_error_when_account_name_is_duplicated(
        self,
        account,
    ):
        accounts = [
            account,
            make_account(
                code="1002",
                name="Cash",
            ),
        ]

        with pytest.raises(ValidationError) as exc_info:
            make_chart_of_accounts(accounts=accounts)

        errors = exc_info.value.errors()

        assert any(
            error["type"] == ErrorCode.DUPLICATE_ACCOUNT_NAME for error in errors
        )

    def test_raises_validation_error_when_account_name_differs_only_by_case(
        self,
        account,
    ):
        accounts = [
            account,
            make_account(
                code="1002",
                name="CASH",
            ),
        ]

        with pytest.raises(ValidationError) as exc_info:
            make_chart_of_accounts(accounts=accounts)

        errors = exc_info.value.errors()

        assert any(
            error["type"] == ErrorCode.DUPLICATE_ACCOUNT_NAME for error in errors
        )
