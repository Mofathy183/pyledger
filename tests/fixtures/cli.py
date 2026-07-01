from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from typer.testing import CliRunner

from pyledger.cli.context import CliContext
from tests.factories import make_fake_cli_context


@pytest.fixture
def cli_runner() -> CliRunner:
    """Typer's CliRunner — shared across every CLI test, unit or integration."""
    return CliRunner()


@pytest.fixture
def fake_cli_context(chart_of_accounts) -> CliContext:
    """Unit-tier context: every repo is a Fake*Repo, zero I/O possible.

    Thin wrapper around make_fake_cli_context(), pre-seeded with
    chart_of_accounts so journal/posting commands that validate account
    references don't need extra setup per test. Tests that need a
    different repo shape should call make_fake_cli_context() directly
    with explicit overrides rather than adding a new fixture.
    """
    return make_fake_cli_context(chart=chart_of_accounts)


@pytest_asyncio.fixture
async def real_cli_context(test_settings, clean_db) -> AsyncGenerator[CliContext]:
    """Integration-tier context: real Mongo, no repo overrides.

    Depends on clean_db the same way mongo_account_repo does — guarantees
    Beanie is initialized and collections are empty before the test runs.
    Depends on the session-scoped test_settings fixture rather than
    constructing TestSettings() inline, consistent with every other
    Mongo-backed fixture in the project.

    This is an async fixture because cleanup requires awaiting
    context.aclose(): the returned CliContext lazily opens its own
    MongoDB connection independent of the session-scoped mongo_connection
    fixture, the first time a test touches a repository through it. That
    connection must be explicitly closed after the test, or it leaks for
    the remaining lifetime of the test process. Teardown runs even if
    the test itself raises, since the yield sits inside try/finally.
    """
    context = CliContext(settings=test_settings)
    try:
        yield context
    finally:
        await context.aclose()
