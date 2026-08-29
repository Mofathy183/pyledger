import pytest
from trutina.cli.context import CliContext
from trutina.cli.features.account.handler import (
    create_account_handler,
    delete_account_handler,
    get_account_handler,
    list_accounts_handler,
    update_account_handler,
)
from trutina.core.account import AccountViewModel, ChartOfAccountsViewModel
from trutina.shared.errors import AppError, ErrorCode

from tests.factories import (
    make_chart_of_accounts,
    make_create_account_input,
    make_update_account_input,
)
from tests.factories.cli import make_fake_cli_context


@pytest.fixture
def seeded_cli_context(seeded_account_repo) -> CliContext:
    """A fake CliContext pre-seeded with one known account.

    Handlers are plain async functions with no Typer/portal dependency,
    so they are exercised directly against a CliContext -- never through
    fake_cli_state/fake_cli_state_with_account, whose BlockingPortal
    exists solely to bridge a synchronous Click command thread into the
    CLI's single event loop. Awaiting a handler coroutine directly on
    pytest-asyncio's own loop while a fixture's portal owns a second,
    separate loop is a cross-loop bug, not a shortcut.

    Built inline from seeded_account_repo (already portal-free) rather
    than adding a new fixture, since the same duplication would recur
    for every future feature (journal, posting) needing the same shape.
    """
    return make_fake_cli_context(account_repo=seeded_account_repo)


@pytest.fixture
def empty_cli_context() -> CliContext:
    """A fake CliContext backed by a genuinely empty chart of accounts.

    `fake_cli_context` (tests/fixtures/cli.py) is NOT empty -- it seeds
    from `chart_of_accounts`, which defaults to a single "Cash"/"1001"
    account via `make_chart_of_accounts()`. Any test that needs a truly
    empty chart (create-into-empty-chart, list-with-no-accounts,
    update/delete-against-unknown-code) must use this fixture instead
    of `fake_cli_context`.
    """
    return make_fake_cli_context(chart=make_chart_of_accounts(accounts=[]))


@pytest.mark.unit
class TestCreateAccountHandler:
    async def test_returns_account_view_model(self, empty_cli_context: CliContext):
        dto = make_create_account_input(code="2001", name="Bank")

        result = await create_account_handler(empty_cli_context, dto)

        assert isinstance(result, AccountViewModel)
        assert result.code == "2001"
        assert result.name == "Bank"

    async def test_persists_account_through_service(
        self, empty_cli_context: CliContext
    ):
        dto = make_create_account_input(code="2001", name="Bank")

        await create_account_handler(empty_cli_context, dto)

        service = await empty_cli_context.get_account_service()
        fetched = await service.get_account("2001")
        assert fetched.name == "Bank"

    async def test_raises_duplicate_account_code(self, seeded_cli_context: CliContext):
        dto = make_create_account_input(code="1001", name="Petty Cash")

        with pytest.raises(AppError) as exc_info:
            await create_account_handler(seeded_cli_context, dto)

        assert exc_info.value.code == ErrorCode.DUPLICATE_ACCOUNT_CODE

    async def test_raises_duplicate_account_name(self, seeded_cli_context: CliContext):
        dto = make_create_account_input(code="2001", name="Cash")

        with pytest.raises(AppError) as exc_info:
            await create_account_handler(seeded_cli_context, dto)

        assert exc_info.value.code == ErrorCode.DUPLICATE_ACCOUNT_NAME


@pytest.mark.unit
class TestGetAccountHandler:
    async def test_finds_account_by_code(self, seeded_cli_context: CliContext):
        result = await get_account_handler(seeded_cli_context, "1001")

        assert isinstance(result, AccountViewModel)
        assert result.code == "1001"
        assert result.name == "Cash"

    async def test_falls_back_to_name_when_code_lookup_misses(
        self, seeded_cli_context: CliContext
    ):
        result = await get_account_handler(seeded_cli_context, "Cash")

        assert isinstance(result, AccountViewModel)
        assert result.code == "1001"
        assert result.name == "Cash"

    async def test_resolves_name_case_insensitively(
        self, seeded_cli_context: CliContext
    ):
        result = await get_account_handler(seeded_cli_context, "cash")

        assert result.code == "1001"

    async def test_raises_unknown_account_when_neither_matches(
        self, seeded_cli_context: CliContext
    ):
        with pytest.raises(AppError) as exc_info:
            await get_account_handler(seeded_cli_context, "Nonexistent")

        assert exc_info.value.code == ErrorCode.UNKNOWN_ACCOUNT


@pytest.mark.unit
class TestListAccountsHandler:
    async def test_returns_chart_view_model(self, seeded_cli_context: CliContext):
        result = await list_accounts_handler(seeded_cli_context)

        assert isinstance(result, ChartOfAccountsViewModel)
        assert len(result.accounts) == 1
        assert result.accounts[0].code == "1001"

    async def test_returns_empty_list_when_no_accounts(
        self, empty_cli_context: CliContext
    ):
        result = await list_accounts_handler(empty_cli_context)

        assert result.accounts == []


@pytest.mark.unit
class TestUpdateAccountHandler:
    async def test_returns_updated_account_view_model(
        self, seeded_cli_context: CliContext
    ):
        dto = make_update_account_input(code="1001", name="Main Cash")

        result = await update_account_handler(seeded_cli_context, dto)

        assert isinstance(result, AccountViewModel)
        assert result.name == "Main Cash"

    async def test_raises_when_account_does_not_exist(
        self, empty_cli_context: CliContext
    ):
        dto = make_update_account_input(code="9999", name="Ghost")

        with pytest.raises(AppError) as exc_info:
            await update_account_handler(empty_cli_context, dto)

        assert exc_info.value.code == ErrorCode.UNKNOWN_ACCOUNT


@pytest.mark.unit
class TestDeleteAccountHandler:
    async def test_deletes_existing_account(self, seeded_cli_context: CliContext):
        result = await delete_account_handler(seeded_cli_context, "1001")

        assert result is None
        service = await seeded_cli_context.get_account_service()
        with pytest.raises(AppError):
            await service.get_account("1001")

    async def test_raises_when_account_does_not_exist(
        self, empty_cli_context: CliContext
    ):
        with pytest.raises(AppError) as exc_info:
            await delete_account_handler(empty_cli_context, "9999")

        assert exc_info.value.code == ErrorCode.UNKNOWN_ACCOUNT
