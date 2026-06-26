from types import SimpleNamespace

import pytest

from pyledger.infrastructure.mongo.account import AccountDocument, MongoAccountRepo
from pyledger.infrastructure.mongo.shared import MongoExecutor
from pyledger.modules.account import AccountRepo
from pyledger.modules.account.schemas import Account, AccountCategory, ChartOfAccounts
from tests.factories import make_account, make_chart_of_accounts


@pytest.fixture
def account() -> Account:
    return make_account()


@pytest.fixture
def chart_of_accounts() -> ChartOfAccounts:
    return make_chart_of_accounts()


@pytest.fixture
def cash_account() -> Account:
    return make_account(code="1001", name="Cash", category=AccountCategory.ASSET)


@pytest.fixture
def revenue_account() -> Account:
    return make_account(
        code="4001", name="Sales Revenue", category=AccountCategory.REVENUE
    )


@pytest.fixture
def mongo_account_repo(clean_db) -> AccountRepo:
    """A MongoAccountRepo instance backed by the clean test database.

    Declares clean_db as a dependency to guarantee:
    1. Beanie is initialized (clean_db depends on beanie_init).
    2. The database is empty before the test runs.

    Returns the abstract AccountRepo type so integration tests are written
    against the contract rather than the implementation. Tests that need
    to verify implementation-specific internals can type-narrow inline.
    """
    return MongoAccountRepo(MongoExecutor())


@pytest.fixture
def stub_account_document_settings(monkeypatch):
    """Let AccountDocument's constructor succeed without init_beanie().

    Document.__init__ unconditionally calls self.get_pymongo_collection(),
    which raises CollectionWasNotInitialized unless init_beanie() has
    registered the model (see beanie/odm/documents.py:1162). _to_document()
    never performs I/O — it only builds the object — so a stub settings
    object is sufficient; we don't need a real collection behind it.

    This relies on Beanie's internal get_settings()/pymongo_collection
    shape and may need revisiting on a Beanie upgrade.
    """
    monkeypatch.setattr(
        AccountDocument,
        "get_settings",
        classmethod(lambda cls: SimpleNamespace(pymongo_collection=None)),
    )
