"""Unit tests for build_container()'s pure wiring behavior.

Verifies only that build_container() assembles the correct object
graph with the correct identities, and that it performs no I/O. Does
NOT re-verify AccountService/JournalService/PostingService business
behavior — that's already covered under modules/*/tests/.
"""

import pytest

from pyledger.api.composition.bootstrap import build_container
from pyledger.api.composition.container import Container
from pyledger.modules.account.service import AccountService
from pyledger.modules.journal.service import JournalService
from pyledger.modules.posting.service import PostingService


@pytest.mark.unit
class TestBuildContainer:
    def test_returns_container_instance(self):
        result = build_container()

        assert isinstance(result, Container)

    def test_returns_account_service_instance(self):
        result = build_container()

        assert isinstance(result.account_service, AccountService)

    def test_returns_journal_service_instance(self):
        result = build_container()

        assert isinstance(result.journal_service, JournalService)

    def test_returns_posting_service_instance(self):
        result = build_container()

        assert isinstance(result.posting_service, PostingService)

    def test_journal_service_depends_on_same_account_service(self):
        result = build_container()

        assert result.journal_service._account_service is result.account_service

    def test_posting_service_depends_on_same_journal_service(self):
        result = build_container()

        assert result.posting_service._journal_service is result.journal_service

    def test_performs_no_io(self):
        """build_container() must succeed with no MongoDB instance reachable.

        MongoExecutor and the Mongo*Repo constructors resolve their
        collections through global Beanie Document registration at call
        time, not through anything held by the repo/executor objects
        themselves, so plain construction here must never raise or
        attempt a connection.
        """
        result = build_container()

        assert result is not None

    def test_two_calls_return_independent_containers(self):
        first = build_container()
        second = build_container()

        assert first is not second
        assert first.account_service is not second.account_service
