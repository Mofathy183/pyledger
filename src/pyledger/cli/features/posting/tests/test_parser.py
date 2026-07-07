import pytest
import typer

from pyledger.cli.features.posting.parser import (
    parse_account_identifier,
    parse_journal_number,
)


@pytest.mark.unit
class TestParseJournalNumber:
    def test_returns_parsed_int(self):
        assert parse_journal_number("42") == 42

    def test_strips_surrounding_whitespace(self):
        assert parse_journal_number("  7  ") == 7

    @pytest.mark.parametrize("raw", ["abc", "12.5", "", "  "])
    def test_raises_bad_parameter_for_invalid_input(self, raw):
        with pytest.raises(typer.BadParameter) as exc_info:
            parse_journal_number(raw)
        assert raw in str(exc_info.value)

    def test_accepts_negative_and_zero_without_business_validation(self):
        assert parse_journal_number("0") == 0
        assert parse_journal_number("-5") == -5


@pytest.mark.unit
class TestParseAccountIdentifier:
    def test_strips_surrounding_whitespace(self):
        assert parse_account_identifier("  Cash  ") == "Cash"

    def test_preserves_casing(self):
        assert parse_account_identifier("CASH") == "CASH"

    def test_returns_empty_string_unchanged(self):
        assert parse_account_identifier("   ") == ""
