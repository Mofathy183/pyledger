from datetime import datetime
from decimal import Decimal

import pytest
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from trutina.cli.features.journal import formatter as journal_fmt
from trutina.core.journal.dtos import JournalLineViewModel, JournalViewModel


def _line_vm(
    account: str = "Cash",
    debit_amount: Decimal = Decimal("100"),
    credit_amount: Decimal = Decimal("0"),
) -> JournalLineViewModel:
    return JournalLineViewModel(
        account=account, debit_amount=debit_amount, credit_amount=credit_amount
    )


def _journal_vm(
    journal_number: int = 1,
    posting_date: datetime = datetime(2025, 1, 1),
    description: str | None = "Test entry",
    lines: list[JournalLineViewModel] | None = None,
    total_debits: Decimal = Decimal("100"),
    total_credits: Decimal = Decimal("100"),
    is_balanced: bool = True,
) -> JournalViewModel:
    if lines is None:
        lines = [
            _line_vm(
                account="Cash", debit_amount=Decimal("100"), credit_amount=Decimal("0")
            ),
            _line_vm(
                account="Sales Revenue",
                debit_amount=Decimal("0"),
                credit_amount=Decimal("100"),
            ),
        ]
    return JournalViewModel(
        journal_number=journal_number,
        posting_date=posting_date,
        description=description,
        lines=lines,
        total_debits=total_debits,
        total_credits=total_credits,
        is_balanced=is_balanced,
    )


def _render(renderable) -> str:
    """Render through the formatter's own themed console.

    Uses journal_fmt.console (the same object print_*() calls) rather
    than a bare rich.console.Console so custom style names like
    "info"/"debit"/"credit" resolve instead of raising a missing-style
    error.
    """
    with journal_fmt.console.capture() as capture:
        journal_fmt.console.print(renderable)
    return capture.get()


def _as_group(renderable) -> Group:
    assert isinstance(renderable, Group)
    return renderable


def _as_text(renderable) -> Text:
    assert isinstance(renderable, Text)
    return renderable


@pytest.mark.unit
class TestBuildJournalEntry:
    def test_returns_panel_titled_journal_entry(self):
        result = journal_fmt.build_journal_entry(_journal_vm())

        assert isinstance(result, Panel)
        assert result.title == "Journal Entry"

    def test_header_lines_reflect_view_model_fields(self):
        vm = _journal_vm(journal_number=7, posting_date=datetime(2024, 6, 15))

        result = journal_fmt.build_journal_entry(vm)
        items = list[RenderableType](_as_group(result.renderable).renderables)

        assert _as_text(items[0]).plain == "Journal Entry  #  7"
        assert _as_text(items[1]).plain == "Posting Date:     2024-06-15"

    def test_includes_lines_table(self):
        result = journal_fmt.build_journal_entry(_journal_vm())
        items = list[RenderableType](_as_group(result.renderable).renderables)

        assert isinstance(items[3], Table)

    def test_shows_description_when_present(self):
        vm = _journal_vm(description="Opening balance")

        result = journal_fmt.build_journal_entry(vm)
        items = list[RenderableType](_as_group(result.renderable).renderables)

        assert _as_text(items[5]).plain == "Opening balance"

    def test_shows_placeholder_when_description_is_none(self):
        vm = _journal_vm(description=None)

        result = journal_fmt.build_journal_entry(vm)
        items = list[RenderableType](_as_group(result.renderable).renderables)

        assert _as_text(items[5]).plain == "No description provided."

    def test_totals_are_styled_success_when_balanced(self):
        vm = _journal_vm(is_balanced=True)

        result = journal_fmt.build_journal_entry(vm)
        items = list[RenderableType](_as_group(result.renderable).renderables)
        totals = _as_text(items[7])

        assert totals.style == "success"

    def test_totals_are_styled_error_when_not_balanced(self):
        vm = _journal_vm(
            is_balanced=False,
            total_debits=Decimal("100"),
            total_credits=Decimal("50"),
        )

        result = journal_fmt.build_journal_entry(vm)
        items = list[RenderableType](_as_group(result.renderable).renderables)
        totals = _as_text(items[7])

        assert totals.style == "error"

    def test_totals_content_reflects_debit_and_credit_amounts(self):
        vm = _journal_vm(
            total_debits=Decimal("250.50"), total_credits=Decimal("250.50")
        )

        result = journal_fmt.build_journal_entry(vm)
        items = list[RenderableType](_as_group(result.renderable).renderables)
        totals = _as_text(items[7])

        assert "250.50" in totals.plain


@pytest.mark.unit
class TestBuildJournalList:
    def test_returns_warning_panel_when_no_entries(self):
        result = journal_fmt.build_journal_list([])
        content = _as_text(result.renderable)

        assert isinstance(result, Panel)
        assert result.title == "Journal Entries"
        assert result.style == "warning"
        assert content.plain == "No journal entries found."

    def test_title_includes_total_entry_count(self):
        entries = [_journal_vm(journal_number=1), _journal_vm(journal_number=2)]

        result = journal_fmt.build_journal_list(entries)

        assert result.title == "Journal Entries  (2 total)"

    def test_returns_panel_containing_a_table_when_entries_exist(self):
        result = journal_fmt.build_journal_list([_journal_vm()])

        assert isinstance(result.renderable, Table)

    def test_rendered_output_includes_every_entry(self):
        entries = [
            _journal_vm(journal_number=1, description="Opening"),
            _journal_vm(journal_number=2, description="Payroll"),
        ]

        output = _render(journal_fmt.build_journal_list(entries))

        assert "1" in output
        assert "Opening" in output
        assert "2" in output
        assert "Payroll" in output


@pytest.mark.unit
class TestPrintFunctions:
    def test_print_journal_entry_renders_the_built_panel(self):
        vm = _journal_vm()
        output = _render(journal_fmt.build_journal_entry(vm))

        with journal_fmt.console.capture() as capture:
            journal_fmt.print_journal_entry(vm)

        assert capture.get() == output

    def test_print_journal_list_renders_the_built_panel(self):
        entries = [_journal_vm()]
        output = _render(journal_fmt.build_journal_list(entries))

        with journal_fmt.console.capture() as capture:
            journal_fmt.print_journal_list(entries)

        assert capture.get() == output


@pytest.mark.unit
class TestIsDebitLine:
    def test_returns_true_for_debit_line(self):
        line = _line_vm(debit_amount=Decimal("100"), credit_amount=Decimal("0"))

        assert journal_fmt._is_debit_line(line) is True

    def test_returns_false_for_credit_line(self):
        line = _line_vm(debit_amount=Decimal("0"), credit_amount=Decimal("100"))

        assert journal_fmt._is_debit_line(line) is False


@pytest.mark.unit
class TestBuildLinesTable:
    def test_creates_table_with_expected_columns(self):
        table = journal_fmt._build_lines_table(_journal_vm(lines=[]))

        headers = [column.header for column in table.columns]

        assert headers == ["Account", "Debit", "Credit"]

    def test_adds_one_row_per_line(self):
        vm = _journal_vm(
            lines=[
                _line_vm(
                    account="Cash",
                    debit_amount=Decimal("100"),
                    credit_amount=Decimal("0"),
                ),
                _line_vm(
                    account="Sales Revenue",
                    debit_amount=Decimal("0"),
                    credit_amount=Decimal("100"),
                ),
            ]
        )

        table = journal_fmt._build_lines_table(vm)

        assert len(table.rows) == 2
