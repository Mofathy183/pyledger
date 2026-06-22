from decimal import Decimal

import pytest
from pydantic import ValidationError

from pyledger.modules.journal.schemas.line import JournalLine
from pyledger.shared.errors import ErrorCode
from tests.factories import make_credit_line, make_debit_line


@pytest.mark.unit
class TestJournalLine:
    def test_accepts_debit_only_line(self):
        line = make_debit_line()

        assert line.account == "Cash"
        assert line.debit_amount > 0
        assert line.credit_amount == 0

    def test_accepts_credit_only_line(self):

        line = make_credit_line()

        assert line.account == "Sales Revenue"
        assert line.credit_amount > 0
        assert line.debit_amount == 0

    def test_accepts_normalized_account_name(self):
        account_name = "  Cash  "

        line = make_debit_line(
            account=account_name,
            amount=Decimal("100"),
        )

        assert line.account == "Cash"

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
        line = JournalLine(
            account="Cash",
            debit_amount=debit_amount,
            credit_amount=credit_amount,
        )

        assert line.debit_amount == debit_amount
        assert line.credit_amount == credit_amount

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
            JournalLine(
                account="Cash",
                debit_amount=debit_amount,
                credit_amount=credit_amount,
            )

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.INVALID_LINE_AMOUNTS for error in errors)

    def test_raises_validation_error_when_account_name_is_blank(
        self,
    ):
        with pytest.raises(ValidationError) as exc_info:
            make_debit_line(
                account="   ",
                amount=Decimal("100"),
            )

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.INVALID_ACCOUNT_NAME for error in errors)

    def test_raises_validation_error_when_account_name_is_too_short(
        self,
    ):
        with pytest.raises(ValidationError) as exc_info:
            JournalLine(
                account="A",
                debit_amount=Decimal("100"),
            )

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.STRING_TOO_SHORT for error in errors)

    def test_raises_validation_error_when_account_name_is_too_long(
        self,
    ):
        account_name = "A" * 101

        with pytest.raises(ValidationError) as exc_info:
            JournalLine(
                account=account_name,
                debit_amount=Decimal("100"),
            )

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.STRING_TOO_LONG for error in errors)

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
        }

        payload[field_name] = Decimal("-1")

        with pytest.raises(ValidationError) as exc_info:
            JournalLine(**payload)

        errors = exc_info.value.errors()

        assert any(
            error["type"] == ErrorCode.GREATER_THAN_EQUAL
            and error["loc"] == (field_name,)
            for error in errors
        )
