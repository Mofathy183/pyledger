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
