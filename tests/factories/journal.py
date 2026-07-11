from datetime import datetime
from decimal import Decimal

from pyledger.modules.account import AccountService
from pyledger.modules.account.schemas import ChartOfAccounts
from pyledger.modules.journal import (
    CreateJournalInput,
    JournalLineInput,
    JournalService,
)
from pyledger.modules.journal.schemas import JournalEntry, JournalLine
from tests.factories import make_fake_account_repo
from tests.fakes import FakeJournalRepo


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


def make_create_journal_input(
    *,
    posting_date: datetime | None = None,
    lines: list[JournalLineInput] | None = None,
    description: str | None = "Test entry",
) -> CreateJournalInput:
    if posting_date is None:
        posting_date = datetime(2025, 1, 1)
    if lines is None:
        lines = [
            JournalLineInput(account="Cash", debit_amount=Decimal("100")),
            JournalLineInput(account="Sales Revenue", credit_amount=Decimal("100")),
        ]
    return CreateJournalInput(
        posting_date=posting_date,
        lines=lines,
        description=description,
    )


def make_fake_journal_repo() -> FakeJournalRepo:
    return FakeJournalRepo()


def make_journal_line_request(
    *,
    account: str = "Cash",
    debit_amount: str = "100",
    credit_amount: str = "0",
) -> dict:
    """Build a single journal-line payload for a create request."""
    return {
        "account": account,
        "debit_amount": debit_amount,
        "credit_amount": credit_amount,
    }


def make_create_journal_entry_request(
    *,
    posting_date: str = "2025-01-01T00:00:00",
    lines: list[dict] | None = None,
    description: str | None = "Test entry",
) -> dict:
    """Build a POST /journal-entries request payload.

    Defaults to a balanced two-line entry (Cash debit 100 / Sales
    Revenue credit 100), mirroring
    `tests/factories/journal.py::make_create_journal_input`'s defaults,
    so tests reading both side by side see the same entry.
    """
    if lines is None:
        lines = [
            make_journal_line_request(account="Cash", debit_amount="100"),
            make_journal_line_request(
                account="Sales Revenue", debit_amount="0", credit_amount="100"
            ),
        ]

    payload: dict = {"posting_date": posting_date, "lines": lines}
    if description is not None:
        payload["description"] = description
    return payload


def make_journal_service(
    *,
    chart: ChartOfAccounts | None = None,
) -> tuple[JournalService, FakeJournalRepo]:
    account_repo = make_fake_account_repo(chart=chart)
    account_service = AccountService(account_repo)

    journal_repo = make_fake_journal_repo()

    service = JournalService(
        repo=journal_repo,
        account_service=account_service,
    )

    return service, journal_repo
