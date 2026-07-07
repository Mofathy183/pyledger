from datetime import datetime
from decimal import Decimal

import pytest
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pyledger.cli.features.posting.formatter import (
    build_postings_list,
    print_postings_list,
)
from pyledger.cli.shared.ui import console
from pyledger.modules.posting.dtos import PostingViewModel


def _posting_vm(
    *,
    account: str = "Cash",
    debit_amount: Decimal | None = Decimal("100"),
    credit_amount: Decimal | None = None,
    journal_number: int = 1,
    posting_date: datetime | None = None,
) -> PostingViewModel:
    if posting_date is None:
        posting_date = datetime(2025, 1, 1)
    return PostingViewModel(
        account=account,
        debit_amount=debit_amount,
        credit_amount=credit_amount,
        journal_number=journal_number,
        posting_date=posting_date,
    )


@pytest.mark.unit
class TestBuildPostingsList:
    def test_returns_panel(self):
        result = build_postings_list([_posting_vm()], title="Some Title")

        assert isinstance(result, Panel)

    def test_uses_supplied_title(self):
        result = build_postings_list([_posting_vm()], title="Postings for Cash")

        assert result.title == "Postings for Cash"

    def test_empty_list_returns_warning_text(self):
        result = build_postings_list([], title="Empty")

        assert isinstance(result.renderable, Text)
        assert "No postings found" in result.renderable.plain
        assert result.style == "warning"

    def test_populated_list_returns_table(self):
        result = build_postings_list(
            [_posting_vm(), _posting_vm(account="Sales Revenue")], title="X"
        )

        assert isinstance(result.renderable, Table)
        assert result.renderable.row_count == 2

    def test_debit_posting_shows_debit_amount_only(self):
        vm = _posting_vm(debit_amount=Decimal("250.00"), credit_amount=None)

        with console.capture() as capture:
            console.print(build_postings_list([vm], title="X"))

        output = capture.get()
        assert "250.00" in output

    def test_credit_posting_shows_credit_amount_only(self):
        vm = _posting_vm(debit_amount=None, credit_amount=Decimal("99.99"))

        with console.capture() as capture:
            console.print(build_postings_list([vm], title="X"))

        output = capture.get()
        assert "99.99" in output

    def test_shows_journal_number_and_date(self):
        vm = _posting_vm(journal_number=7, posting_date=datetime(2024, 6, 15))

        with console.capture() as capture:
            console.print(build_postings_list([vm], title="X"))

        output = capture.get()
        assert "7" in output
        assert "2024-06-15" in output


@pytest.mark.unit
class TestPrintPostingsList:
    def test_matches_build_output(self):
        vms = [
            _posting_vm(),
            _posting_vm(
                account="Sales Revenue", debit_amount=None, credit_amount=Decimal("100")
            ),
        ]

        with console.capture() as build_capture:
            console.print(build_postings_list(vms, title="Same Title"))

        with console.capture() as print_capture:
            print_postings_list(vms, title="Same Title")

        assert build_capture.get() == print_capture.get()
