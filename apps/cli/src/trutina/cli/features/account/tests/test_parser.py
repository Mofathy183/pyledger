import pytest
import typer
from pydantic import ValidationError
from trutina.cli.features.account.parser import (
    parse_create_account,
    parse_update_account,
)
from trutina.core.account import CreateAccountInput, UpdateAccountInput
from trutina.core.account.schemas.account import AccountCategory
from trutina.shared.errors import ErrorCode


def assert_has_error_code(exc: ValidationError, code: ErrorCode) -> None:
    """Assert that a ValidationError contains the expected error code."""
    assert any(error["type"] == code for error in exc.errors())


@pytest.mark.unit
class TestParseCreateAccount:
    def test_creates_input_with_valid_values(self):
        result = parse_create_account(
            code="1001",
            name="Cash",
            category="asset",
        )

        assert isinstance(result, CreateAccountInput)
        assert result.code == "1001"
        assert result.name == "Cash"
        assert result.category is AccountCategory.ASSET

    def test_normalizes_all_inputs(self):
        result = parse_create_account(
            code=" 1001 ",
            name=" Cash ",
            category=" asset ",
        )

        assert result.code == "1001"
        assert result.name == "Cash"
        assert result.category is AccountCategory.ASSET

    @pytest.mark.parametrize(
        "raw_category",
        [
            "asset",
            "Asset",
            "ASSET",
            "aSsEt",
            " asset ",
        ],
    )
    def test_resolves_category_case_insensitively(self, raw_category):
        result = parse_create_account(
            code="1001",
            name="Cash",
            category=raw_category,
        )

        assert result.category is AccountCategory.ASSET

    @pytest.mark.parametrize(
        ("raw_category", "expected"),
        [
            ("asset", AccountCategory.ASSET),
            ("liability", AccountCategory.LIABILITY),
            ("equity", AccountCategory.EQUITY),
            ("revenue", AccountCategory.REVENUE),
            ("expense", AccountCategory.EXPENSE),
            ("dividend", AccountCategory.DIVIDEND),
            ("drawing", AccountCategory.DRAWING),
        ],
    )
    def test_resolves_every_category_member(self, raw_category, expected):
        result = parse_create_account(
            code="1001",
            name="Cash",
            category=raw_category,
        )

        assert result.category is expected

    def test_raises_bad_parameter_for_invalid_category(self):
        with pytest.raises(typer.BadParameter) as exc_info:
            parse_create_account(
                code="1001",
                name="Cash",
                category="bogus",
            )

        message = str(exc_info.value)

        assert "'bogus'" in message
        assert "valid category" in message
        assert "Choose from:" in message
        assert "Asset" in message

    def test_raises_bad_parameter_for_whitespace_only_category(self):
        with pytest.raises(typer.BadParameter):
            parse_create_account(
                code="1001",
                name="Cash",
                category="   ",
            )

    def test_raises_validation_error_when_code_is_whitespace_only(self):
        with pytest.raises(ValidationError) as exc_info:
            parse_create_account(
                code="   ",
                name="Cash",
                category="asset",
            )

        assert_has_error_code(exc_info.value, ErrorCode.STRING_TOO_SHORT)

    def test_raises_validation_error_when_name_is_whitespace_only(self):
        with pytest.raises(ValidationError) as exc_info:
            parse_create_account(
                code="1001",
                name="   ",
                category="asset",
            )

        assert_has_error_code(exc_info.value, ErrorCode.STRING_TOO_SHORT)

    def test_raises_validation_error_when_name_is_single_character(self):
        with pytest.raises(ValidationError) as exc_info:
            parse_create_account(
                code="1001",
                name=" A ",
                category="asset",
            )

        assert_has_error_code(exc_info.value, ErrorCode.STRING_TOO_SHORT)


@pytest.mark.unit
class TestParseUpdateAccount:
    def test_creates_input_with_only_code(self):
        result = parse_update_account(code="1001")

        assert isinstance(result, UpdateAccountInput)
        assert result.code == "1001"
        assert result.name is None
        assert result.category is None

    def test_creates_input_with_name_and_category(self):
        result = parse_update_account(
            code="1001",
            name="Main Cash",
            category="asset",
        )

        assert result.code == "1001"
        assert result.name == "Main Cash"
        assert result.category is AccountCategory.ASSET

    def test_returns_none_name_when_name_not_provided(self):
        result = parse_update_account(
            code="1001",
            name=None,
        )

        assert result.name is None

    def test_returns_none_category_when_category_not_provided(self):
        result = parse_update_account(
            code="1001",
            category=None,
        )

        assert result.category is None

    def test_normalizes_code_and_name(self):
        result = parse_update_account(
            code=" 1001 ",
            name=" Main Cash ",
        )

        assert result.code == "1001"
        assert result.name == "Main Cash"

    @pytest.mark.parametrize(
        ("raw_category", "expected"),
        [
            ("asset", AccountCategory.ASSET),
            ("liability", AccountCategory.LIABILITY),
            ("equity", AccountCategory.EQUITY),
            ("revenue", AccountCategory.REVENUE),
            ("expense", AccountCategory.EXPENSE),
            ("dividend", AccountCategory.DIVIDEND),
            ("drawing", AccountCategory.DRAWING),
            (" Revenue ", AccountCategory.REVENUE),
        ],
    )
    def test_resolves_category_when_provided(self, raw_category, expected):
        result = parse_update_account(
            code="1001",
            category=raw_category,
        )

        assert result.category is expected

    def test_does_not_resolve_category_when_omitted(self):
        result = parse_update_account(
            code="1001",
            name="Main Cash",
            category=None,
        )

        assert result.name == "Main Cash"
        assert result.category is None

    def test_raises_bad_parameter_for_invalid_category(self):
        with pytest.raises(typer.BadParameter) as exc_info:
            parse_update_account(
                code="1001",
                category="bogus",
            )

        message = str(exc_info.value)

        assert "'bogus'" in message
        assert "valid category" in message
        assert "Choose from:" in message
        assert "Asset" in message

    def test_raises_bad_parameter_for_whitespace_only_category(self):
        with pytest.raises(typer.BadParameter):
            parse_update_account(
                code="1001",
                category="   ",
            )

    def test_raises_validation_error_when_name_is_whitespace_only(self):
        with pytest.raises(ValidationError) as exc_info:
            parse_update_account(
                code="1001",
                name="   ",
            )

        assert_has_error_code(exc_info.value, ErrorCode.STRING_TOO_SHORT)
