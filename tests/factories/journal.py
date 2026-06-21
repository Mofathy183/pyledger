from datetime import datetime
from decimal import Decimal

from pyledger.modules.journal.schemas.journal import JournalEntry
from pyledger.modules.journal.schemas.line import JournalLine


def make_debit_line(
    account: str = "Cash",
    amount: Decimal = Decimal("100"),
) -> JournalLine:
    return JournalLine(
        account=account,
        debit_amount=amount,
    )


def make_credit_line(
    account: str = "Sales Revenue",
    amount: Decimal = Decimal("100"),
) -> JournalLine:
    return JournalLine(
        account=account,
        credit_amount=amount,
    )


def make_journal_entry(
    *,
    journal_number: int = 1,
    posting_date: datetime | None = None,
    lines: list[JournalLine] | None = None,
    description: str | None = "Test entry",
) -> JournalEntry:
    if posting_date is None:
        posting_date = datetime(2025, 1, 1)

    if lines is None:
        lines = [
            make_debit_line(),
            make_credit_line(),
        ]

    return JournalEntry(
        journal_number=journal_number,
        posting_date=posting_date,
        lines=lines,
        description=description,
    )
