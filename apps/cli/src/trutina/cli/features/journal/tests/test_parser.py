from datetime import datetime
from decimal import Decimal

import pytest
import typer
from pydantic import ValidationError
from trutina.cli.features.journal.parser import (
    parse_create_journal,
    parse_journal_line,
    parse_line_spec,
    parse_posting_date,
)
from trutina.core.journal.dtos import CreateJournalInput, JournalLineInput
from trutina.shared.errors import ErrorCode
from trutina.shared.util import default_posting_date


def assert_has_error_code(exc: ValidationError, code: ErrorCode) -> None:
    """Assert that a ValidationError contains the expected error code."""
    assert any(error["type"] == code for error in exc.errors())


@pytest.mark.unit
class TestParsePostingDate:
    def test_returns_todays_date_when_none(self):
        result = parse_posting_date(None)

        assert result.date() == default_posting_date().date()

    def test_returns_todays_date_when_blank(self):
        result = parse_posting_date("   ")

        assert result.date() == default_posting_date().date()

    def test_parses_valid_date_string(self):
        result = parse_posting_date("2024-06-15")

        assert result == datetime(2024, 6, 15)

    def test_raises_bad_parameter_for_invalid_format(self):
        with pytest.raises(typer.BadParameter) as exc_info:
            parse_posting_date("06/15/2024")

        message = str(exc_info.value)
        assert "'06/15/2024'" in message
        assert "YYYY-MM-DD" in message

    def test_raises_bad_parameter_for_garbage_input(self):
        with pytest.raises(typer.BadParameter):
            parse_posting_date("not-a-date")


@pytest.mark.unit
class TestParseJournalLine:
    def test_builds_debit_line(self):
        result = parse_journal_line(
            account="Cash", debit_amount="100", credit_amount="0"
        )

        assert isinstance(result, JournalLineInput)
        assert result.account == "Cash"
        assert result.debit_amount == Decimal("100")
        assert result.credit_amount == Decimal("0")

    def test_builds_credit_line(self):
        result = parse_journal_line(
            account="Sales Revenue", debit_amount="0", credit_amount="100"
        )

        assert result.debit_amount == Decimal("0")
        assert result.credit_amount == Decimal("100")

    def test_defaults_amounts_to_zero_when_omitted(self):
        result = parse_journal_line(account="Cash")

        assert result.debit_amount == Decimal("0")
        assert result.credit_amount == Decimal("0")

    def test_normalizes_account_whitespace(self):
        result = parse_journal_line(account="  Cash  ", debit_amount="100")

        assert result.account == "Cash"

    def test_raises_bad_parameter_for_invalid_debit_amount(self):
        with pytest.raises(typer.BadParameter) as exc_info:
            parse_journal_line(account="Cash", debit_amount="abc")

        assert "not a valid decimal amount" in str(exc_info.value)

    def test_raises_bad_parameter_for_invalid_credit_amount(self):
        with pytest.raises(typer.BadParameter):
            parse_journal_line(account="Cash", credit_amount="abc")

    def test_raises_validation_error_when_account_name_is_too_short(self):
        with pytest.raises(ValidationError) as exc_info:
            parse_journal_line(account="A", debit_amount="100")

        assert_has_error_code(exc_info.value, ErrorCode.STRING_TOO_SHORT)

    def test_raises_validation_error_when_amount_is_negative(self):
        with pytest.raises(ValidationError) as exc_info:
            parse_journal_line(account="Cash", debit_amount="-1")

        assert_has_error_code(exc_info.value, ErrorCode.GREATER_THAN_EQUAL)


@pytest.mark.unit
class TestParseLineSpec:
    def test_parses_debit_line(self):
        result = parse_line_spec("Cash:100:0")

        assert result.account == "Cash"
        assert result.debit_amount == Decimal("100")
        assert result.credit_amount == Decimal("0")

    def test_parses_credit_line_with_blank_debit_segment(self):
        result = parse_line_spec("Sales Revenue::100")

        assert result.account == "Sales Revenue"
        assert result.debit_amount == Decimal("0")
        assert result.credit_amount == Decimal("100")

    def test_raises_bad_parameter_when_not_three_segments(self):
        with pytest.raises(typer.BadParameter) as exc_info:
            parse_line_spec("Cash:100")

        message = str(exc_info.value)
        assert "'Cash:100'" in message
        assert "Account:Debit:Credit" in message

    def test_raises_bad_parameter_for_too_many_segments(self):
        with pytest.raises(typer.BadParameter):
            parse_line_spec("Cash:100:0:extra")

    def test_raises_bad_parameter_for_invalid_amount_segment(self):
        with pytest.raises(typer.BadParameter):
            parse_line_spec("Cash:abc:0")


@pytest.mark.unit
class TestParseCreateJournal:
    def test_builds_input_with_valid_values(self):
        lines = [
            parse_journal_line(account="Cash", debit_amount="100"),
            parse_journal_line(account="Sales Revenue", credit_amount="100"),
        ]

        result = parse_create_journal(
            posting_date="2024-06-15",
            lines=lines,
            description="Opening balance",
        )

        assert isinstance(result, CreateJournalInput)
        assert result.posting_date == datetime(2024, 6, 15)
        assert len(result.lines) == 2
        assert result.description == "Opening balance"

    def test_defaults_posting_date_to_today_when_none(self):
        lines = [
            parse_journal_line(account="Cash", debit_amount="100"),
            parse_journal_line(account="Sales Revenue", credit_amount="100"),
        ]

        result = parse_create_journal(posting_date=None, lines=lines)

        assert result.posting_date.date() == default_posting_date().date()

    def test_normalizes_description_whitespace(self):
        lines = [
            parse_journal_line(account="Cash", debit_amount="100"),
            parse_journal_line(account="Sales Revenue", credit_amount="100"),
        ]

        result = parse_create_journal(
            posting_date=None, lines=lines, description="  Opening balance  "
        )

        assert result.description == "Opening balance"

    def test_returns_none_description_when_omitted(self):
        lines = [
            parse_journal_line(account="Cash", debit_amount="100"),
            parse_journal_line(account="Sales Revenue", credit_amount="100"),
        ]

        result = parse_create_journal(posting_date=None, lines=lines, description=None)

        assert result.description is None

    def test_raises_validation_error_when_fewer_than_two_lines(self):
        lines = [parse_journal_line(account="Cash", debit_amount="100")]

        with pytest.raises(ValidationError) as exc_info:
            parse_create_journal(posting_date=None, lines=lines)

        assert_has_error_code(exc_info.value, ErrorCode.TOO_SHORT)

    def test_raises_bad_parameter_for_invalid_posting_date(self):
        lines = [
            parse_journal_line(account="Cash", debit_amount="100"),
            parse_journal_line(account="Sales Revenue", credit_amount="100"),
        ]

        with pytest.raises(typer.BadParameter):
            parse_create_journal(posting_date="not-a-date", lines=lines)
