import pytest
from pydantic import ValidationError

from pyledger.modules.account.schemas.account import (
    AccountCategory,
)
from pyledger.shared.errors import ErrorCode
from tests.factories import make_account


@pytest.mark.unit
class TestAccount:
    def test_creates_account_with_valid_values(self, account):
        assert account.code == "1001"
        assert account.name == "Cash"
        assert account.category is AccountCategory.ASSET

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
    def test_returns_normal_balance_from_category(
        self,
        category,
        expected_balance,
    ):
        account = make_account(category=category)

        result = account.normal_balance

        assert result == expected_balance

    @pytest.mark.parametrize(
        "invalid_name",
        [
            "",
            " ",
        ],
    )
    def test_raises_validation_error_when_name_is_too_short(
        self,
        invalid_name,
    ):
        with pytest.raises(ValidationError) as exc_info:
            make_account(name=invalid_name)

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.STRING_TOO_SHORT for error in errors)

    def test_raises_validation_error_when_name_is_whitespace_only(self):
        with pytest.raises(ValidationError) as exc_info:
            make_account(name="   ")

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.INVALID_ACCOUNT_NAME for error in errors)

    @pytest.mark.parametrize(
        "invalid_code",
        [
            "1000!",
            "1000@",
            "1000#",
            "1000$",
            "1000/",
        ],
    )
    def test_raises_validation_error_when_code_contains_invalid_characters(
        self,
        invalid_code,
    ):
        with pytest.raises(ValidationError) as exc_info:
            make_account(code=invalid_code)

        errors = exc_info.value.errors()

        assert any(error["type"] == "string_pattern_mismatch" for error in errors)

    def test_returns_normalized_account_name(self):
        account = make_account(name="  Cash  ")

        assert account.name == "Cash"

    def test_raises_validation_error_when_name_exceeds_max_length(self):
        invalid_name = "A" * 151

        with pytest.raises(ValidationError) as exc_info:
            make_account(name=invalid_name)

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.STRING_TOO_LONG for error in errors)

    def test_raises_validation_error_when_code_exceeds_max_length(self):
        invalid_code = "A" * 21

        with pytest.raises(ValidationError) as exc_info:
            make_account(code=invalid_code)

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.STRING_TOO_LONG for error in errors)
