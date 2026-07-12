from pyledger.cli.context import CliContext
from pyledger.config import TestSettings
from pyledger.core.account import AccountRepo
from pyledger.core.account.schemas import ChartOfAccounts
from pyledger.core.journal import JournalRepo
from pyledger.core.posting import PostingRepo

from tests.factories.account import make_fake_account_repo
from tests.factories.journal import make_fake_journal_repo
from tests.factories.posting import make_fake_posting_repo


def make_fake_cli_context(
    *,
    account_repo: AccountRepo | None = None,
    journal_repo: JournalRepo | None = None,
    posting_repo: PostingRepo | None = None,
    chart: ChartOfAccounts | None = None,
) -> CliContext:
    """Build a CliContext wired entirely to Fake*Repo instances.

    Every repository defaults to its Fake* implementation, so a context
    returned by this factory can never open a MongoDB connection.

    Args:
        account_repo: Explicit AccountRepo to inject. Defaults to a
            fresh FakeAccountRepo seeded with `chart`.
        journal_repo: Explicit JournalRepo to inject. Defaults to a
            fresh FakeJournalRepo.
        posting_repo: Explicit PostingRepo to inject. Defaults to a
            fresh FakePostingRepo.
        chart: Optional ChartOfAccounts used to seed the default
            FakeAccountRepo. Ignored when `account_repo` is supplied
            directly.

    Returns:
        A CliContext with every repository faked, safe for unit tests.
    """
    return CliContext(
        settings=TestSettings(),
        account_repo=account_repo or make_fake_account_repo(chart=chart),
        journal_repo=journal_repo or make_fake_journal_repo(),
        posting_repo=posting_repo or make_fake_posting_repo(),
    )
