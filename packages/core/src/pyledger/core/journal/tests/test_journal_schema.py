from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError
from pyledger.shared.errors import ErrorCode

from tests.factories import (
    make_credit_line,
    make_debit_line,
    make_journal_entry,
)


@pytest.mark.unit
class TestJournalEntry:
    def test_creates_balanced_entry(self):
        lines = [
            make_debit_line(),
            make_credit_line(),
        ]

        entry = make_journal_entry(lines=lines)

        assert entry.is_balanced is True
        assert entry.total_debits == Decimal("100")
        assert entry.total_credits == Decimal("100")

    def test_accepts_three_or_more_lines(self):
        lines = [
            make_debit_line(amount=Decimal("150")),
            make_credit_line(amount=Decimal("100")),
            make_credit_line(
                account="Accounts Receivable",
                amount=Decimal("50"),
            ),
        ]

        entry = make_journal_entry(lines=lines)

        assert len(entry.lines) == 3
        assert entry.is_balanced is True

    def test_accepts_positive_journal_number(self):
        entry = make_journal_entry(journal_number=1)

        assert entry.journal_number == 1

    def test_accepts_posting_date_after_supported_period_start(
        self,
    ):
        posting_date = datetime(2020, 1, 2)

        entry = make_journal_entry(posting_date=posting_date)

        assert entry.posting_date == posting_date

    @pytest.mark.parametrize(
        ("debit_amount", "credit_amount"),
        [
            (Decimal("100.00"), Decimal("99.99")),
            (Decimal("100.01"), Decimal("100.00")),
            (Decimal("200.00"), Decimal("100.00")),
        ],
    )
    def test_raises_validation_error_when_lines_are_unbalanced(
        self,
        debit_amount,
        credit_amount,
    ):
        lines = [
            make_debit_line(amount=debit_amount),
            make_credit_line(amount=credit_amount),
        ]

        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(lines=lines)

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.UNBALANCED_ENTRY for error in errors)

    def test_raises_validation_error_when_fewer_than_two_lines(
        self,
    ):
        lines = [
            make_debit_line(),
        ]

        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(lines=lines)

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.TOO_SHORT for error in errors)

    def test_raises_validation_error_when_posting_date_is_in_future(
        self,
    ):
        future_date = datetime(9999, 1, 1)

        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(posting_date=future_date)

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.FUTURE_DATE for error in errors)

    def test_raises_validation_error_when_posting_date_is_before_supported_period(
        self,
    ):
        posting_date = datetime(2020, 1, 1)

        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(posting_date=posting_date)

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.GREATER_THAN for error in errors)

    def test_raises_validation_error_when_journal_number_is_not_positive(
        self,
    ):
        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(journal_number=0)

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.GREATER_THAN for error in errors)

    def test_accepts_description_when_provided(self):
        description = "Purchased office equipment"

        entry = make_journal_entry(description=description)

        assert entry.description == description

    def test_accepts_description_as_none(self):
        entry = make_journal_entry(description=None)

        assert entry.description is None

    def test_raises_validation_error_when_description_exceeds_max_length(
        self,
    ):
        description = "A" * 256

        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(description=description)

        errors = exc_info.value.errors()

        assert any(error["type"] == ErrorCode.STRING_TOO_LONG for error in errors)

    def test_calculates_total_debits(self):
        lines = [
            make_debit_line(amount=Decimal("100")),
            make_debit_line(
                account="Equipment",
                amount=Decimal("250"),
            ),
            make_credit_line(amount=Decimal("350")),
        ]

        entry = make_journal_entry(lines=lines)

        assert entry.total_debits == Decimal("350")

    def test_calculates_total_credits(self):
        lines = [
            make_debit_line(amount=Decimal("350")),
            make_credit_line(amount=Decimal("100")),
            make_credit_line(
                account="Accounts Payable",
                amount=Decimal("250"),
            ),
        ]

        entry = make_journal_entry(lines=lines)

        assert entry.total_credits == Decimal("350")
