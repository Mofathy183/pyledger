from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from pyledger.core.errors import ErrorCode
from pyledger.core.models.journal import JournalEntry, JournalLine
from tests.helpers import make_credit_line, make_debit_line, make_journal_entry


@pytest.mark.unit
class TestJournalLine:
    def test_creates_valid_journal_line(self, debit_line, credit_line):
        assert isinstance(debit_line, JournalLine)
        assert isinstance(credit_line, JournalLine)

        assert debit_line.credit_amount == Decimal("0")
        assert credit_line.debit_amount == Decimal("0")

    def test_accepts_and_normalizes_account_name(self):
        account_name = "  Cash  "

        line = make_debit_line(account=account_name)

        assert line.account == "Cash"

    def test_raises_validation_error_when_account_exceeds_max_length(self):
        with pytest.raises(ValidationError) as exc_info:
            make_credit_line(account="A" * 105)

        errors = exc_info.value.errors()
        assert errors[0]["type"] == ErrorCode.STRING_TOO_LONG
        assert errors[0]["loc"][0] == "account"

    def test_raises_validation_error_when_account_is_shorter_than_min_length(self):
        with pytest.raises(ValidationError) as exc_info:
            make_credit_line(account="A")

        errors = exc_info.value.errors()
        assert errors[0]["type"] == ErrorCode.STRING_TOO_SHORT
        assert errors[0]["loc"][0] == "account"

    @pytest.mark.parametrize(
        "account",
        [
            "123Cash",
            "Cash&&&&Bank",
            "PP&&&&&&&E",
            "Owner'''''''''s Equity",
        ],
    )
    def test_raises_validation_error_when_account_name_is_invalid(
        self,
        account,
    ):
        with pytest.raises(ValidationError) as exc_info:
            make_debit_line(account=account)

        errors = exc_info.value.errors()
        assert errors[0]["type"] == ErrorCode.INVALID_ACCOUNT_NAME
        assert errors[0]["loc"][0] == "account"

    @pytest.mark.parametrize(
        "line, field",
        [
            (make_debit_line, "debit_amount"),
            (make_credit_line, "credit_amount"),
        ],
    )
    def test_raises_validation_error_when_amount_is_negative(self, line, field):
        with pytest.raises(ValidationError) as exc_info:
            line(amount=Decimal("-500"))

        errors = exc_info.value.errors()

        assert errors[0]["type"] == ErrorCode.GREATER_THAN_EQUAL
        assert errors[0]["loc"][0] == field

    def test_raises_validation_error_when_both_amounts_are_positive(self):
        with pytest.raises(ValidationError) as exc_info:
            JournalLine(
                account="Cash",
                debit_amount=Decimal("100"),
                credit_amount=Decimal("100"),
            )

        errors = exc_info.value.errors()
        assert errors[0]["type"] == ErrorCode.INVALID_LINE_AMOUNTS

    def test_raises_validation_error_when_both_amounts_are_zero(self):
        with pytest.raises(ValidationError) as exc_info:
            JournalLine(
                account="Cash",
                debit_amount=Decimal("0"),
                credit_amount=Decimal("0"),
            )

        errors = exc_info.value.errors()
        assert errors[0]["type"] == ErrorCode.INVALID_LINE_AMOUNTS


@pytest.mark.unit
class TestJournalEntry:
    def test_creates_valid_journal_entry(self, journal_entry):
        assert isinstance(journal_entry, JournalEntry)

        assert len(journal_entry.lines) >= 2

        assert journal_entry.is_balanced is True
        assert journal_entry.total_debits == Decimal("100")
        assert journal_entry.total_credits == Decimal("100")

    def test_returns_correct_totals_for_multiple_lines(self):
        entry = make_journal_entry(
            lines=[
                make_debit_line(account="Cash", amount=Decimal("1500")),
                make_debit_line(account="A/R", amount=Decimal("3500")),
                make_debit_line(account="PP&E", amount=Decimal("6_000")),
                make_credit_line(account="A/P", amount=Decimal("11_000")),
            ]
        )

        assert entry.total_debits == Decimal("11000")
        assert entry.total_credits == Decimal("11000")
        assert entry.is_balanced is True

    def test_accepts_none_description(self):
        entry = make_journal_entry(description=None)

        assert entry.description is None

    @pytest.mark.parametrize(
        "number",
        [0, -5],
    )
    def test_raises_validation_error_when_invalid_journal_number(self, number):
        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(journal_number=number)

        errors = exc_info.value.errors()
        assert errors[0]["type"] == ErrorCode.GREATER_THAN
        assert errors[0]["loc"][0] == "journal_number"

    @pytest.mark.parametrize(
        "date",
        [
            datetime(year=2019, month=1, day=1),
            datetime(year=2015, month=1, day=1),
            datetime(year=1919, month=1, day=1),
            datetime(year=2009, month=1, day=1),
        ],
    )
    def test_raises_validation_error_when_posting_date_is_before_minimum_date(
        self, date
    ):
        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(posting_date=date)

        errors = exc_info.value.errors()
        assert errors[0]["type"] == ErrorCode.GREATER_THAN
        assert errors[0]["loc"][0] == "posting_date"

    def test_raises_validation_error_when_posting_date_equals_minimum_date(
        self,
    ):
        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(posting_date=datetime(2020, 1, 1))

        errors = exc_info.value.errors()
        assert errors[0]["type"] == ErrorCode.GREATER_THAN
        assert errors[0]["loc"][0] == "posting_date"

    def test_raises_validation_error_when_posting_date_is_in_the_future(
        self,
    ):
        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(posting_date=datetime.now() + timedelta(days=15))

        errors = exc_info.value.errors()
        assert errors[0]["type"] == ErrorCode.FUTURE_DATE
        assert errors[0]["loc"][0] == "posting_date"

    def test_raises_validation_error_when_description_exceeds_max_length(self):
        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(description=300 * "H")

        errors = exc_info.value.errors()
        assert errors[0]["type"] == ErrorCode.STRING_TOO_LONG
        assert errors[0]["loc"][0] == "description"

    def test_raises_validation_error_when_entry_has_fewer_than_two_lines(
        self, debit_line
    ):
        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(lines=[debit_line])

        errors = exc_info.value.errors()
        assert errors[0]["type"] == ErrorCode.TOO_SHORT
        assert errors[0]["loc"][0] == "lines"

    def test_raises_validation_error_when_entry_is_unbalanced(self):
        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(
                lines=[
                    make_debit_line(amount=Decimal("1500")),
                    make_credit_line(amount=Decimal("3500")),
                ]
            )
        errors = exc_info.value.errors()

        assert errors[0]["type"] == ErrorCode.UNBALANCED_ENTRY
