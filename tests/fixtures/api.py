"""Shared API-layer test fixtures.

Phase 1 of the API testing foundation (see `PyLedger API Testing
Architecture`, Section 4). This module intentionally implements only
the fixtures needed to test the composition root
(`api/composition/{container,app,dependencies,bootstrap}.py`):

    fake_container
    api_app
    api_client
    real_api_app
    real_api_client

`override_service`, `json_request`, and `assert_error_response` are
deliberately deferred to Phase 3, once the first real router exists —
building them now would mean guessing a response envelope shape that
doesn't exist yet.

Fixtures are layered so each depends only on the one before it,
mirroring the CLI's own fake/real fixture split
(`tests/fixtures/cli.py`):

    fake_container -> api_app -> api_client
    test_settings + mongo_connection + clean_db -> real_api_app -> real_api_client

Unit-tier fixtures (`fake_container`, `api_app`, `api_client`) never
touch MongoDB — `api_app` attaches `fake_container` to
`app.state.container` directly and never enters `create_app()`'s real
lifespan, so no connection is ever opened.

Integration-tier fixtures (`real_api_app`, `real_api_client`) enter the
real lifespan from `bootstrap.make_lifespan()` against `test_settings`,
backed by `clean_db` (which in turn depends on `beanie_init` and
`mongo_connection`), mirroring `real_cli_state` in
`tests/fixtures/cli.py`.

Known gap: `asgi-lifespan` (the usual `LifespanManager` package) is not
listed in `pyproject.toml`'s dev dependency group as of this PR. Rather
than adding an unconfirmed dependency, `real_api_app` drives the
lifespan directly via `FastAPI`'s own `router.lifespan_context(app)`
async context manager, which requires no extra package. If
`asgi-lifespan` is later added intentionally, this fixture can switch
to `LifespanManager` with no change to `real_api_client` or any
downstream test.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from pyledger.api.composition.app import create_app
from pyledger.api.composition.container import Container
from pyledger.config import TestSettings
from pyledger.modules.account.service import AccountService
from pyledger.modules.journal.service import JournalService
from pyledger.modules.posting.service import PostingService
from tests.factories import (
    make_fake_account_repo,
    make_fake_journal_repo,
    make_fake_posting_repo,
)


@pytest.fixture
def fake_container() -> Container:
    """A Container built entirely from Fake*Repo-backed services.

    Mirrors `tests/factories/cli.py::make_fake_cli_context()`'s pattern
    for the API's `Container` shape, and wires services identically to
    `build_container()` in `api/composition/bootstrap.py`:
    JournalService depends on AccountService, PostingService depends on
    JournalService. No repository here can open a MongoDB connection,
    so nothing built on top of this fixture can perform I/O.
    """
    account_repo = make_fake_account_repo()
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

    return Container(
        account_service=account_service,
        journal_service=journal_service,
        posting_service=posting_service,
    )


@pytest.fixture
def api_app(fake_container: Container) -> FastAPI:
    """A FastAPI app built via create_app(), with no lifespan entered.

    `create_app()` still attaches the real `make_lifespan(settings)` to
    the app, but that lifespan is never entered here — the app object
    is used directly, and `fake_container` is attached to
    `app.state.container` by hand, exactly the way `fake_cli_context`
    bypasses `CliContext`'s lazy connection machinery entirely. No
    MongoDB connection is ever opened by this fixture.
    """
    app = create_app(TestSettings())
    app.state.container = fake_container
    return app


@pytest.fixture
def api_client(api_app: FastAPI) -> AsyncClient:
    """An httpx.AsyncClient over api_app via ASGITransport, no lifespan.

    The unit-tier client every fake-backed route/composition test uses.
    Uses ASGITransport rather than binding a real port, since there is
    no reason to listen on a socket in tests.
    """
    transport = ASGITransport(app=api_app)
    return AsyncClient(transport=transport, base_url="http://testserver")


@pytest.fixture
def api_client_no_raise(api_app: FastAPI) -> AsyncClient:
    transport = ASGITransport(
        app=api_app,
        raise_app_exceptions=False,
    )
    return AsyncClient(
        transport=transport,
        base_url="http://testserver",
    )


@pytest_asyncio.fixture
async def real_api_app(
    test_settings: TestSettings,
    clean_db,
) -> AsyncGenerator[FastAPI]:
    """A FastAPI app with the real lifespan entered, backed by clean_db.

    Declares `clean_db` as a dependency to guarantee Beanie is
    initialized and the database is empty before the app's own
    lifespan runs `init_beanie()` again and opens its own connection —
    this mirrors `real_cli_state`'s documented second-connection
    pattern in `tests/fixtures/cli.py`, with the same caveat: entering
    this lifespan opens a second MongoDB client bound to this
    fixture's own event loop and re-registers the Document classes
    globally.

    `router.lifespan_context(app)` is FastAPI/Starlette's own lifespan
    context manager — used directly here instead of `asgi-lifespan`'s
    `LifespanManager`, since that package is not currently a declared
    dev dependency (see module docstring).
    """
    app = create_app(test_settings)

    async with app.router.lifespan_context(app):
        yield app


@pytest_asyncio.fixture
async def real_api_client(real_api_app: FastAPI) -> AsyncGenerator[AsyncClient]:
    """An httpx.AsyncClient over real_api_app, real lifespan already entered.

    The integration-tier client every Mongo-backed route/composition
    test uses. `real_api_app` has already opened its connection and
    populated `app.state.container` by the time this client is used.
    """
    transport = ASGITransport(app=real_api_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
