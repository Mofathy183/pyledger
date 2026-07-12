"""In-memory PostingRepo implementation for PostingService unit tests.

Provides a lightweight fake that satisfies the PostingRepo contract without
any storage backend. Test cases inspect ``saved_batches`` to verify that
the service persisted the correct records.
"""

from pyledger.core.posting.repo import PostingRepo
from pyledger.core.posting.schemas.ledger_posting import LedgerPosting
from pyledger.shared.rule import account_lookup_key


class FakePostingRepo(PostingRepo):
    """In-memory PostingRepo for PostingService unit tests.

    This fake behaves according to the PostingRepo contract and provides
    lightweight inspection hooks for assertions.

    All postings are stored in a flat list. Both ``get_by_account`` and
    ``get_by_journal_number`` perform linear scans over that list, which
    is appropriate for unit tests where the data set is small.

    ``get_by_account`` applies case-insensitive matching via
    ``account_lookup_key``, consistent with how ``FakeAccountRepo``
    handles account name lookups.

    Attributes:
        saved_batches: Each list passed to ``save_many``, in call order.
            Tests assert on ``saved_batches[0]`` to verify the batch
            size and on ``saved_batches`` length to verify the number
            of save calls.
    """

    def __init__(self) -> None:
        self._postings: list[LedgerPosting] = []
        self.saved_batches: list[list[LedgerPosting]] = []

    async def save_many(self, postings: list[LedgerPosting]) -> None:
        self.saved_batches.append(list(postings))
        self._postings.extend(postings)

    async def get_by_account(self, account: str) -> list[LedgerPosting]:
        key = account_lookup_key(account)
        return [p for p in self._postings if account_lookup_key(p.account) == key]

    async def get_by_journal_number(self, journal_number: int) -> list[LedgerPosting]:
        return [p for p in self._postings if p.journal_number == journal_number]
