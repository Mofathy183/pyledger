from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from pyledger.modules.posting.schemas.ledger_posting import LedgerPosting
from pyledger.shared.errors import ErrorCode
from tests.factories import make_debit_posting


@pytest.mark.unit
class TestLedgerPosting:
    def test_creates_valid_debit_posting(self, debit_posting):
        assert debit_posting.account == "Cash"
        assert debit_posting.debit_amount == Decimal("100")
        assert debit_posting.credit_amount == Decimal("0")
        assert debit_posting.journal_number == 1

    def test_creates_valid_credit_posting(self, credit_posting):
        assert credit_posting.account == "Sales Revenue"
        assert credit_posting.credit_amount == Decimal("100")
        assert credit_posting.debit_amount == Decimal("0")
        assert credit_posting.journal_number == 1

    def test_is_debit_returns_true_for_debit_posting(self, debit_posting):
        assert debit_posting.is_debit is True

    def test_is_debit_returns_false_for_credit_posting(self, credit_posting):
        assert credit_posting.is_debit is False

    def test_accepts_normalized_account_name(self):
        posting = make_debit_posting(account="  Cash  ")

        assert posting.account == "Cash"

    def test_accepts_minimum_valid_posting_date(self):
        posting_date = datetime(2020, 1, 2)

        posting = make_debit_posting(posting_date=posting_date)

        assert posting.posting_date == posting_date

    @pytest.mark.parametrize(
        ("debit_amount", "credit_amount"),
        [
            (Decimal("0.01"), Decimal("0")),
            (Decimal("0"), Decimal("0.01")),
        ],
    )
    def test_accepts_positive_amount_boundary(
        self,
        debit_amount,
        credit_amount,
    ):
        posting = LedgerPosting(
            account="Cash",
            debit_amount=debit_amount,
            credit_amount=credit_amount,
            journal_number=1,
            posting_date=datetime(2025, 1, 1),
        )

        assert posting.debit_amount == debit_amount
        assert posting.credit_amount == credit_amount

    @pytest.mark.parametrize(
        ("debit_amount", "credit_amount"),
        [
            (Decimal("0"), Decimal("0")),
            (Decimal("100"), Decimal("100")),
        ],
    )
    def test_raises_validation_error_when_line_amounts_are_invalid(
        self,
        debit_amount,
        credit_amount,
    ):
        with pytest.raises(ValidationError) as exc_info:
            LedgerPosting(
                account="Cash",
                debit_amount=debit_amount,
                credit_amount=credit_amount,
                journal_number=1,
                posting_date=datetime(2025, 1, 1),
            )

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.INVALID_LINE_AMOUNTS for error in errors)

    @pytest.mark.parametrize(
        "field_name",
        [
            "debit_amount",
            "credit_amount",
        ],
    )
    def test_raises_validation_error_when_amount_is_negative(
        self,
        field_name,
    ):
        payload = {
            "account": "Cash",
            "debit_amount": Decimal("0"),
            "credit_amount": Decimal("0"),
            "journal_number": 1,
            "posting_date": datetime(2025, 1, 1),
        }

        payload[field_name] = Decimal("-1")

        with pytest.raises(ValidationError) as exc_info:
            LedgerPosting(**payload)

        errors = exc_info.value.errors()

        assert any(
            error["type"] == ErrorCode.GREATER_THAN_EQUAL
            and error["loc"] == (field_name,)
            for error in errors
        )

    def test_raises_validation_error_when_account_name_is_blank(self):
        with pytest.raises(ValidationError) as exc_info:
            make_debit_posting(account="   ")

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.INVALID_ACCOUNT_NAME for error in errors)

    def test_raises_validation_error_when_account_name_contains_invalid_characters(
        self,
    ):
        with pytest.raises(ValidationError) as exc_info:
            make_debit_posting(account="Cash@@")

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.INVALID_ACCOUNT_NAME for error in errors)

    def test_raises_validation_error_when_account_name_is_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            LedgerPosting(
                account="A",
                debit_amount=Decimal("100"),
                journal_number=1,
                posting_date=datetime(2025, 1, 1),
            )

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.STRING_TOO_SHORT for error in errors)

    def test_raises_validation_error_when_account_name_is_too_long(self):
        account_name = "A" * 101

        with pytest.raises(ValidationError) as exc_info:
            LedgerPosting(
                account=account_name,
                debit_amount=Decimal("100"),
                journal_number=1,
                posting_date=datetime(2025, 1, 1),
            )

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.STRING_TOO_LONG for error in errors)

    @pytest.mark.parametrize(
        "journal_number",
        [0, -1],
    )
    def test_raises_validation_error_when_journal_number_is_not_positive(
        self,
        journal_number,
    ):
        with pytest.raises(ValidationError) as exc_info:
            make_debit_posting(journal_number=journal_number)

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.GREATER_THAN for error in errors)

    def test_raises_validation_error_when_posting_date_is_in_future(self):
        future_date = datetime(9999, 1, 1)

        with pytest.raises(ValidationError) as exc_info:
            make_debit_posting(posting_date=future_date)

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.FUTURE_DATE for error in errors)

    def test_raises_validation_error_when_posting_date_is_before_supported_period(
        self,
    ):
        posting_date = datetime(2020, 1, 1)

        with pytest.raises(ValidationError) as exc_info:
            make_debit_posting(posting_date=posting_date)

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.GREATER_THAN for error in errors)

    def test_raises_when_frozen_field_is_mutated(self):
        posting = make_debit_posting()

        with pytest.raises(ValidationError) as exc_info:
            posting.account = "Equipment"

        errors = exc_info.value.errors()

        assert any(error["type"] == "frozen_instance" for error in errors)
