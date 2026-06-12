from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from pyledger.core.errors import ERRORS
from pyledger.utils.constants import FIELD_LABELS, HINTS, ErrorCode
from pyledger.utils.formatter import (
    FormattedJournalEntry,
    FormattedJournalLine,
    format_journal_entry,
    format_validation_errors,
    get_error_detail,
)
from tests.helpers import make_credit_line, make_debit_line, make_journal_entry


@pytest.mark.unit
class TestGetErrorDetail:
    def test_returns_error_for_known_error_type(self):
        error = {
            "type": ErrorCode.STRING_TOO_LONG,
        }

        result = get_error_detail(error)

        assert result.detail.code == ErrorCode.STRING_TOO_LONG
        assert result.detail.message == ERRORS[ErrorCode.STRING_TOO_LONG].message
        assert result.hint == HINTS[ErrorCode.STRING_TOO_LONG]

    def test_returns_unknown_error_for_unrecognized_error_type(self):
        error = {
            "type": "",
        }

        result = get_error_detail(error)

        assert result.detail.code == ErrorCode.UNKNOWN_ERROR
        assert result.detail.message == ERRORS[ErrorCode.UNKNOWN_ERROR].message
        assert result.hint == HINTS[ErrorCode.UNKNOWN_ERROR]


@pytest.mark.unit
class TestFormatValidationErrors:
    def test_returns_formatted_error_for_single_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(posting_date=datetime.now() + timedelta(days=5))

        result = format_validation_errors(exc_info.value)[0]

        assert result.field == "posting_date"
        assert result.detail.code == ErrorCode.FUTURE_DATE
        assert result.detail.message == ERRORS[ErrorCode.FUTURE_DATE].message
        assert result.hint == HINTS[ErrorCode.FUTURE_DATE]

    def test_returns_formatted_errors_for_multiple_validation_errors(self):
        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(
                journal_number=0,
                posting_date=datetime(year=2019, month=12, day=31),
                lines=[],
            )

        result = format_validation_errors(exc_info.value)

        assert len(result) == 3

        fields = {error.field for error in result}

        assert "journal_number" in fields
        assert "posting_date" in fields
        assert "lines" in fields

    def test_returns_field_label_for_model_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            make_journal_entry(
                lines=[
                    make_debit_line(amount=Decimal("500")),
                    make_credit_line(amount=Decimal("300")),
                ]
            )

        result = format_validation_errors(exc_info.value)[0]

        assert result.field == FIELD_LABELS[ErrorCode.UNBALANCED_ENTRY]
        assert result.detail.code == ErrorCode.UNBALANCED_ENTRY


@pytest.mark.unit
class TestFormattedJournalEntry:
    def test_returns_formatted_journal_entry(self, journal_entry):
        result = format_journal_entry(journal_entry)

        assert isinstance(result, FormattedJournalEntry)

        assert result.journal_number == 1
        assert result.posting_date == "2025-01-01"

        assert result.total_debits == "100.00"
        assert result.total_credits == "100.00"

        assert result.is_balanced is True

    def test_formats_journal_lines(self, balanced_lines):
        entry = make_journal_entry(lines=balanced_lines)

        result = format_journal_entry(entry)

        debit_line = result.lines[0]
        credit_line = result.lines[1]

        assert isinstance(result.lines[0], FormattedJournalLine)

        assert debit_line.debit == "100.00"
        assert debit_line.credit == ""
        assert debit_line.is_debit is True

        assert credit_line.debit == ""
        assert credit_line.credit == "100.00"
        assert credit_line.is_debit is False

    def test_returns_default_description_when_description_is_none(self):
        entry = make_journal_entry(description=None)

        result = format_journal_entry(entry)

        assert result.description == "No description provided."
