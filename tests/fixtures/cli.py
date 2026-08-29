"""Test fixtures for the CLI layer, unit and integration tier."""

from collections.abc import AsyncGenerator, Iterator

import pytest
import pytest_asyncio
from anyio.from_thread import start_blocking_portal
from beanie import init_beanie
from trutina.cli.context import CliContext
from trutina.cli.state import CliState
from trutina.config import TestSettings
from typer.testing import CliRunner

from tests.factories import make_fake_cli_context
from tests.fixtures.mongo import DOCUMENT_MODELS


@pytest.fixture
def cli_runner() -> CliRunner:
    """Typer's CliRunner — shared across every CLI test, unit or integration."""
    return CliRunner()


@pytest.fixture
def fake_cli_context(chart_of_accounts) -> CliContext:
    """Unit-tier context: every repo is a Fake*Repo, zero I/O possible."""
    return make_fake_cli_context(chart=chart_of_accounts)


@pytest.fixture
def fake_cli_state(fake_cli_context: CliContext) -> Iterator[CliState]:
    """Unit-tier CliState: fake_cli_context paired with a real portal.

    No Mongo involved, so there's no loop-binding hazard.
    """
    with start_blocking_portal(backend="asyncio") as portal:
        state = CliState(context=fake_cli_context, portal=portal)
        try:
            yield state
        finally:
            portal.call(fake_cli_context.aclose)


@pytest_asyncio.fixture
async def real_cli_context(test_settings, clean_db) -> AsyncGenerator[CliContext]:
    """Integration-tier context for direct `await`-based CliContext tests
    ONLY (accessor caching, aclose() idempotency, override precedence,
    ConnectionFailure -> AppError.storage_unavailable()). Do NOT pair
    this with a portal — see real_cli_state's docstring for why.
    """
    context = CliContext(settings=test_settings)
    try:
        yield context
    finally:
        await context.aclose()


@pytest_asyncio.fixture
async def real_cli_state(
    test_settings: TestSettings,
    clean_db,
    mongo_connection,
) -> AsyncGenerator[CliState]:
    """Integration-tier CliState: real MongoDB, entirely portal-owned.

    CliContext._get_connection() calls init_beanie() unconditionally on
    first use, and init_beanie() mutates GLOBAL class-level state on
    AccountDocument/JournalDocument/PostingDocument — it is not scoped
    to a connection or a fixture. Because Typer command dispatch is
    synchronous, the CliContext built here only ever gets used from
    inside the portal's own thread and event loop (via state.call()),
    so its lazy bootstrap opens a SECOND MongoDB client, bound to that
    portal's loop, and re-registers the Document classes against it —
    globally overwriting the registration the session-scoped
    mongo_connection/beanie_init fixtures already set up for every
    other integration test.

    That second connection closes correctly at the end of this fixture
    (via portal.call(context.aclose)), but nothing else re-points the
    Document classes back at the original, still-open session
    connection afterward. Left alone, every subsequent test in the
    session that touches AccountDocument/JournalDocument/PostingDocument
    — even tests with no relationship to the CLI — fails with
    "Cannot use AsyncMongoClient in different event loop", because the
    class-level registration is left pointing at this fixture's now-
    closed, foreign-loop client.

    The explicit init_beanie() call after the `with` block exits is not
    optional cleanup — it is what prevents this fixture from corrupting
    the rest of the test session. It re-registers the Document classes
    against mongo_connection.db (the untouched, still-alive, session-
    loop-bound connection already established by mongo_connection/
    beanie_init) so later tests see a consistent, working registration
    again, regardless of test order. DOCUMENT_MODELS is imported from
    tests/fixtures/mongo.py rather than redeclared, so this can't
    silently drift if a fourth Document class is ever added there.

    This is a pragmatic test-layer fix, not a structural one. The real
    gap is that CliContext has no constructor seam for "attach to an
    already-connected Mongo/Beanie setup" the way it already does for
    account_repo=/journal_repo=/posting_repo= overrides — that would let
    integration tests avoid opening a second connection at all. Flagging
    rather than changing context.py silently.
    """
    context = CliContext(settings=test_settings)
    with start_blocking_portal(backend="asyncio") as portal:
        state = CliState(context=context, portal=portal)
        try:
            yield state
        finally:
            portal.call(context.aclose)

    await init_beanie(database=mongo_connection.db, document_models=DOCUMENT_MODELS)
