from datetime import datetime
from decimal import Decimal

from trutina.core.account import AccountService
from trutina.core.account.schemas import AccountCategory, ChartOfAccounts
from trutina.core.journal import JournalService
from trutina.core.posting import PostingService
from trutina.core.posting.schemas.ledger_posting import LedgerPosting

from tests.factories.account import make_fake_account_repo
from tests.factories.journal import make_fake_journal_repo
from tests.fakes import FakePostingRepo

from .account import make_account, make_chart_of_accounts


def make_debit_posting(
    *,
    account: str = "Cash",
    amount: Decimal = Decimal("100"),
    journal_number: int = 1,
    posting_date: datetime | None = None,
) -> LedgerPosting:
    if posting_date is None:
        posting_date = datetime(2025, 1, 1)
    return LedgerPosting(
        account=account,
        debit_amount=amount,
        journal_number=journal_number,
        posting_date=posting_date,
    )


def make_credit_posting(
    *,
    account: str = "Sales Revenue",
    amount: Decimal = Decimal("100"),
    journal_number: int = 1,
    posting_date: datetime | None = None,
) -> LedgerPosting:
    if posting_date is None:
        posting_date = datetime(2025, 1, 1)
    return LedgerPosting(
        account=account,
        credit_amount=amount,
        journal_number=journal_number,
        posting_date=posting_date,
    )


def make_fake_posting_repo() -> FakePostingRepo:
    return FakePostingRepo()


def make_posting_feature_chart() -> ChartOfAccounts:
    """The Cash / Sales Revenue chart every default journal input balances against.

    Mirrors _simple_chart() in modules/posting/tests/test_service_unit.py.
    """
    return make_chart_of_accounts(
        accounts=[
            make_account(code="1001", name="Cash", category=AccountCategory.ASSET),
            make_account(
                code="4001",
                name="Sales Revenue",
                category=AccountCategory.REVENUE,
            ),
        ]
    )


def make_posting_service(
    *,
    chart: ChartOfAccounts | None = None,
) -> tuple[PostingService, JournalService, FakePostingRepo]:
    account_repo = make_fake_account_repo(chart=chart)
    account_service = AccountService(account_repo)

    journal_repo = make_fake_journal_repo()
    journal_service = JournalService(
        repo=journal_repo,
        account_service=account_service,
    )

    posting_repo = make_fake_posting_repo()
    posting_service = PostingService(
        repo=posting_repo,
        journal_service=journal_service,
    )

    return posting_service, journal_service, posting_repo
