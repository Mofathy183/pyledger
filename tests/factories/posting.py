from datetime import datetime
from decimal import Decimal

from pyledger.modules.posting.schemas.ledger_posting import LedgerPosting


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
