"""Fixtures wiring real feature services to real MongoDB repositories.

These exist solely for service-integration tests under
``modules/*/tests/test_service_integration.py``. Unlike the unit-test
fixtures in ``tests/fixtures/{account,journal,posting}.py`` (which inject
``Fake*Repo`` instances), this module wires each service to its concrete
Mongo adapter, mirroring the production dependency graph:

    AccountService -> MongoAccountRepo
    JournalService -> MongoJournalRepo, AccountService
    PostingService -> MongoPostingRepo, JournalService

``services`` depends on ``mongo_account_repo``, ``mongo_journal_repo``, and
``mongo_posting_repo`` — all three depend on ``clean_db``, so requesting all
three together does not collide: ``clean_db`` truncates every collection
once per test regardless of how many repo fixtures pull it in.
"""

import pytest
from trutina.core.account.schemas.account import AccountCategory
from trutina.core.account.service import AccountService
from trutina.core.journal.service import JournalService
from trutina.core.posting.service import PostingService

from tests.factories import make_create_account_input


@pytest.fixture
def services(mongo_account_repo, mongo_journal_repo, mongo_posting_repo):
    """Real services wired to real Mongo repositories.

    Returns a ``(account_service, journal_service, posting_service)`` tuple
    so tests can compose whichever subset of the workflow they need without
    repeating the wiring inline.
    """
    account_service = AccountService(mongo_account_repo)
    journal_service = JournalService(
        repo=mongo_journal_repo,
        account_service=account_service,
    )
    posting_service = PostingService(
        repo=mongo_posting_repo,
        journal_service=journal_service,
    )
    return account_service, journal_service, posting_service


@pytest.fixture
async def simple_accounts(services):
    """Seed the two accounts that the default journal/posting factories expect.

    ``make_create_journal_input()`` (and therefore ``make_debit_line()`` /
    ``make_credit_line()``) defaults to "Cash" and "Sales Revenue" — this
    fixture creates exactly those two accounts through the real
    ``AccountService`` so journal/posting workflow tests can rely on the
    default factory input without re-seeding the chart in every test.

    Returns the wired ``AccountService`` for tests that need to make
    additional assertions against it.
    """
    account_service, _journal_service, _posting_service = services

    await account_service.create_account(
        make_create_account_input(code="1001", name="Cash")
    )
    await account_service.create_account(
        make_create_account_input(
            code="4001",
            name="Sales Revenue",
            category=AccountCategory.REVENUE,
        )
    )

    return account_service
