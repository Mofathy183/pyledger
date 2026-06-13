import pytest
from pydantic import ValidationError

from pyledger.core.errors import ErrorCode
from pyledger.core.models.account import AccountCategory
from tests.helpers import make_account


@pytest.mark.unit
class TestAccount:
    def test_creates_account_with_valid_data(self, account):
        assert account.code == 1001
        assert account.name == "Cash"
        assert account.category == AccountCategory.ASSET
        assert account.aliases == []

    def test_accepts_empty_aliases(self, account):
        assert account.aliases == []

    def test_returns_normalized_name(self):
        account = make_account(
            name="    Cash    ",
            aliases=[
                "   Bank Account   ",
                " Main Cash ",
            ],
        )

        assert account.name == "Cash"
        assert account.aliases == [
            "Bank Account",
            "Main Cash",
        ]

    def test_raises_validation_error_when_name_is_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            make_account(name="!!!")

        errors = exc_info.value.errors()[0]
        assert errors["type"] == ErrorCode.INVALID_ACCOUNT_NAME
        assert errors["loc"][0] == "name"

    def test_raises_validation_error_when_alias_is_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            make_account(
                aliases=[
                    "Bank Account",
                    "!!!",
                ],
            )

        errors = exc_info.value.errors()[0]
        assert errors["type"] == ErrorCode.INVALID_ACCOUNT_NAME
        assert errors["loc"][0] == "aliases"

    def test_raises_validation_error_when_code_is_zero(self):
        with pytest.raises(ValidationError) as exc_info:
            make_account(code=0)

        errors = exc_info.value.errors()[0]
        assert errors["type"] == ErrorCode.GREATER_THAN
        assert errors["loc"][0] == "code"

    def test_raises_validation_error_when_code_is_negative(self):
        with pytest.raises(ValidationError) as exc_info:
            make_account(code=-1011)

        errors = exc_info.value.errors()[0]
        assert errors["type"] == ErrorCode.GREATER_THAN
        assert errors["loc"][0] == "code"

    def test_raises_validation_error_when_more_than_five_aliases_are_provided(self):
        with pytest.raises(ValidationError) as exc_info:
            make_account(
                aliases=[
                    "Alias 1",
                    "Alias 2",
                    "Alias 3",
                    "Alias 4",
                    "Alias 5",
                    "Alias 6",
                ],
            )

        errors = exc_info.value.errors()[0]
        assert errors["type"] == ErrorCode.TOO_LONG
        assert errors["loc"][0] == "aliases"

    @pytest.mark.parametrize(
        ("category", "expected_balance"),
        [
            (AccountCategory.ASSET, "debit"),
            (AccountCategory.EXPENSE, "debit"),
            (AccountCategory.DRAWING, "debit"),
            (AccountCategory.LIABILITY, "credit"),
            (AccountCategory.EQUITY, "credit"),
            (AccountCategory.REVENUE, "credit"),
            (AccountCategory.DIVIDEND, "credit"),
        ],
    )
    def test_returns_normal_balance_from_category(self, category, expected_balance):
        account = make_account(category=category)

        assert account.normal_balance == expected_balance
