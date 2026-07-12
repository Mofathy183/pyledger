import pytest
from pydantic import ValidationError
from pyledger.core.account.dtos import (
    AccountViewModel,
    ChartOfAccountsViewModel,
    CreateAccountInput,
    UpdateAccountInput,
)
from pyledger.core.account.schemas.account import AccountCategory
from pyledger.shared.errors import ErrorCode


@pytest.mark.unit
class TestCreateAccountInput:
    def test_creates_with_valid_values(self):
        dto = CreateAccountInput(
            code="1001",
            name="Cash",
            category=AccountCategory.ASSET,
        )

        assert dto.code == "1001"
        assert dto.name == "Cash"
        assert dto.category is AccountCategory.ASSET

    @pytest.mark.parametrize(
        "field_name, value",
        [
            ("code", ""),
            ("name", ""),
            ("name", "A"),
        ],
    )
    def test_raises_validation_error_when_string_length_is_too_short(
        self,
        field_name,
        value,
    ):
        payload = {
            "code": "1001",
            "name": "Cash",
            "category": AccountCategory.ASSET,
        }

        payload[field_name] = value

        with pytest.raises(ValidationError) as exc_info:
            CreateAccountInput(**payload)

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.STRING_TOO_SHORT for error in errors)

    def test_raises_validation_error_when_code_exceeds_max_length(self):
        code = "1" * 21

        with pytest.raises(ValidationError) as exc_info:
            CreateAccountInput(
                code=code,
                name="Cash",
                category=AccountCategory.ASSET,
            )

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.STRING_TOO_LONG for error in errors)

    def test_raises_validation_error_when_name_exceeds_max_length(self):
        name = "A" * 151

        with pytest.raises(ValidationError) as exc_info:
            CreateAccountInput(
                code="1001",
                name=name,
                category=AccountCategory.ASSET,
            )

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.STRING_TOO_LONG for error in errors)


@pytest.mark.unit
class TestUpdateAccountInput:
    def test_creates_with_only_required_code(self):
        dto = UpdateAccountInput(
            code="1001",
        )

        assert dto.code == "1001"
        assert dto.name is None
        assert dto.category is None

    def test_accepts_name_update(self):
        dto = UpdateAccountInput(
            code="1001",
            name="Operating Cash",
        )

        assert dto.name == "Operating Cash"

    def test_accepts_category_update(self):
        dto = UpdateAccountInput(
            code="1001",
            category=AccountCategory.EXPENSE,
        )

        assert dto.category is AccountCategory.EXPENSE

    def test_accepts_explicit_none_values(self):
        dto = UpdateAccountInput(
            code="1001",
            name=None,
            category=None,
        )

        assert dto.name is None
        assert dto.category is None

    @pytest.mark.parametrize(
        "field_name, value",
        [
            ("code", ""),
            ("name", ""),
            ("name", "A"),
        ],
    )
    def test_raises_validation_error_when_string_length_is_too_short(
        self,
        field_name,
        value,
    ):
        payload = {
            "code": "1001",
            "name": "Cash",
        }
        payload[field_name] = value

        with pytest.raises(ValidationError) as exc_info:
            UpdateAccountInput(**payload)  # type: ignore

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.STRING_TOO_SHORT for error in errors)

    def test_raises_validation_error_when_code_exceeds_max_length(self):
        code = "1" * 21

        with pytest.raises(ValidationError) as exc_info:
            UpdateAccountInput(code=code)

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.STRING_TOO_LONG for error in errors)

    def test_raises_validation_error_when_name_exceeds_max_length(self):
        name = "A" * 151

        with pytest.raises(ValidationError) as exc_info:
            UpdateAccountInput(
                code="1001",
                name=name,
            )

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.STRING_TOO_LONG for error in errors)


@pytest.mark.unit
class TestAccountViewModel:
    def test_creates_with_valid_values(self):
        view_model = AccountViewModel(
            code="1001",
            name="Cash",
            category=AccountCategory.ASSET,
            normal_balance="debit",
        )

        assert view_model.code == "1001"
        assert view_model.name == "Cash"
        assert view_model.category is AccountCategory.ASSET
        assert view_model.normal_balance == "debit"


@pytest.mark.unit
class TestChartOfAccountsViewModel:
    def test_creates_with_accounts(self):
        account = AccountViewModel(
            code="1001",
            name="Cash",
            category=AccountCategory.ASSET,
            normal_balance="debit",
        )

        # Act
        chart = ChartOfAccountsViewModel(
            accounts=[account],
        )

        assert len(chart.accounts) == 1
        assert chart.accounts[0] == account

    def test_creates_with_empty_accounts(self):
        chart = ChartOfAccountsViewModel(accounts=[])

        assert chart.accounts == []
