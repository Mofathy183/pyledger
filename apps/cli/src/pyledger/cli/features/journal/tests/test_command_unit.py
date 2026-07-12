from collections.abc import Iterator

import pytest
from anyio.from_thread import start_blocking_portal
from pyledger.cli.app import app
from pyledger.cli.shared.ui import console
from pyledger.cli.state import CliState
from pyledger.core.account.schemas.account import AccountCategory
from typer.testing import CliRunner

from tests.factories import make_account, make_chart_of_accounts
from tests.factories.cli import make_fake_cli_context


def _simple_chart():
    """Cash/Sales Revenue -- the default account names baked into every
    --line/interactive test in this file, mirroring JournalService's
    own `_simple_chart()` test helper.
    """
    return make_chart_of_accounts(
        accounts=[
            make_account(code="1001", name="Cash", category=AccountCategory.ASSET),
            make_account(
                code="4001", name="Sales Revenue", category=AccountCategory.REVENUE
            ),
        ]
    )


@pytest.fixture
def journal_cli_state() -> Iterator[CliState]:
    """CliState backed by a chart seeded with Cash/Sales Revenue and an
    empty journal ledger.

    Built locally rather than pulled from a shared fixture -- no
    "seeded-with-accounts" CliState fixture is confirmed to exist for
    Journal yet. Mirrors the same self-contained pattern
    `empty_cli_state` uses in the Account command unit tests.
    """
    context = make_fake_cli_context(chart=_simple_chart())
    with start_blocking_portal(backend="asyncio") as portal:
        state = CliState(context=context, portal=portal)
        try:
            yield state
        finally:
            portal.call(context.aclose)


def _invoke(
    runner: CliRunner, state: CliState, args: list[str], input: str | None = None
):
    """Invoke the CLI app with a fake CliState and capture console output.

    Mirrors the account command tests' _invoke() helper exactly.
    """
    with console.capture() as capture:
        result = runner.invoke(app, args, obj=state, input=input)
    return result, capture.get()


@pytest.mark.unit
class TestCreateCommandFlagMode:
    def test_creates_balanced_entry_and_exits_zero(
        self, cli_runner: CliRunner, journal_cli_state: CliState
    ):
        result, output = _invoke(
            cli_runner,
            journal_cli_state,
            [
                "journal",
                "create",
                "--line",
                "Cash:100:0",
                "--line",
                "Sales Revenue:0:100",
            ],
        )

        assert result.exit_code == 0
        assert "Cash" in output
        assert "Sales Revenue" in output
        assert "100.00" in output

    def test_assigns_sequential_journal_numbers(
        self, cli_runner: CliRunner, journal_cli_state: CliState
    ):
        args = [
            "journal",
            "create",
            "--line",
            "Cash:100:0",
            "--line",
            "Sales Revenue:0:100",
        ]

        first, first_output = _invoke(cli_runner, journal_cli_state, args)
        second, second_output = _invoke(cli_runner, journal_cli_state, args)

        assert first.exit_code == 0
        assert second.exit_code == 0
        assert "#  1" in first_output
        assert "#  2" in second_output

    def test_accepts_posting_date_and_description_options(
        self, cli_runner: CliRunner, journal_cli_state: CliState
    ):
        result, output = _invoke(
            cli_runner,
            journal_cli_state,
            [
                "journal",
                "create",
                "--posting-date",
                "2024-06-15",
                "--description",
                "Opening balance",
                "--line",
                "Cash:100:0",
                "--line",
                "Sales Revenue:0:100",
            ],
        )

        assert result.exit_code == 0
        assert "2024-06-15" in output
        assert "Opening balance" in output

    def test_malformed_line_spec_exits_with_usage_error(
        self, cli_runner: CliRunner, journal_cli_state: CliState
    ):
        result, _ = _invoke(
            cli_runner,
            journal_cli_state,
            [
                "journal",
                "create",
                "--line",
                "Cash:100",
                "--line",
                "Sales Revenue:0:100",
            ],
        )

        assert result.exit_code == 2

    def test_invalid_amount_in_line_spec_exits_with_usage_error(
        self, cli_runner: CliRunner, journal_cli_state: CliState
    ):
        result, _ = _invoke(
            cli_runner,
            journal_cli_state,
            [
                "journal",
                "create",
                "--line",
                "Cash:abc:0",
                "--line",
                "Sales Revenue:0:100",
            ],
        )

        assert result.exit_code == 2

    def test_fewer_than_two_lines_renders_validation_error_and_exits_one(
        self, cli_runner: CliRunner, journal_cli_state: CliState
    ):
        result, output = _invoke(
            cli_runner,
            journal_cli_state,
            ["journal", "create", "--line", "Cash:100:0"],
        )

        assert result.exit_code == 1
        assert "Validation Error" in output or "too_short" in output

    def test_unknown_account_renders_error_panel_and_exits_one(
        self, cli_runner: CliRunner, journal_cli_state: CliState
    ):
        result, output = _invoke(
            cli_runner,
            journal_cli_state,
            [
                "journal",
                "create",
                "--line",
                "Ghost Account:100:0",
                "--line",
                "Sales Revenue:0:100",
            ],
        )

        assert result.exit_code == 1
        assert "account.unknown" in output or "Validation Error" in output

    def test_unbalanced_entry_renders_validation_error_and_exits_one(
        self, cli_runner: CliRunner, journal_cli_state: CliState
    ):
        result, output = _invoke(
            cli_runner,
            journal_cli_state,
            [
                "journal",
                "create",
                "--line",
                "Cash:100:0",
                "--line",
                "Sales Revenue:0:50",
            ],
        )

        assert result.exit_code == 1
        assert "Validation Error" in output or "journal.unbalanced" in output


@pytest.mark.unit
class TestCreateCommandInteractiveMode:
    def test_prompts_for_all_fields_and_creates_balanced_entry(
        self, cli_runner: CliRunner, journal_cli_state: CliState
    ):
        input_lines = (
            "2024-06-15\n"  # posting date
            "Cash\n100\n0\n"  # line 1: account, debit, credit
            "Sales Revenue\n0\n100\n"  # line 2: account, debit, credit
            "n\n"  # decline another line
            "Opening balance\n"  # description
        )

        result, output = _invoke(
            cli_runner, journal_cli_state, ["journal", "create"], input=input_lines
        )

        assert result.exit_code == 0
        assert "Cash" in output
        assert "Sales Revenue" in output
        assert "Opening balance" in output


@pytest.mark.unit
class TestGetCommand:
    def test_finds_entry_by_journal_number_argument(
        self, cli_runner: CliRunner, journal_cli_state: CliState
    ):
        _invoke(
            cli_runner,
            journal_cli_state,
            [
                "journal",
                "create",
                "--line",
                "Cash:100:0",
                "--line",
                "Sales Revenue:0:100",
            ],
        )

        result, output = _invoke(cli_runner, journal_cli_state, ["journal", "get", "1"])

        assert result.exit_code == 0
        assert "#  1" in output

    def test_prompts_for_journal_number_when_omitted(
        self, cli_runner: CliRunner, journal_cli_state: CliState
    ):
        _invoke(
            cli_runner,
            journal_cli_state,
            [
                "journal",
                "create",
                "--line",
                "Cash:100:0",
                "--line",
                "Sales Revenue:0:100",
            ],
        )

        result, output = _invoke(
            cli_runner, journal_cli_state, ["journal", "get"], input="1\n"
        )

        assert result.exit_code == 0
        assert "#  1" in output

    def test_unknown_journal_number_renders_error_panel_and_exits_one(
        self, cli_runner: CliRunner, journal_cli_state: CliState
    ):
        result, output = _invoke(
            cli_runner, journal_cli_state, ["journal", "get", "999"]
        )

        assert result.exit_code == 1
        assert "journal.unknown_entry" in output or "Validation Error" in output


@pytest.mark.unit
class TestListCommand:
    def test_lists_created_entries(
        self, cli_runner: CliRunner, journal_cli_state: CliState
    ):
        _invoke(
            cli_runner,
            journal_cli_state,
            [
                "journal",
                "create",
                "--line",
                "Cash:100:0",
                "--line",
                "Sales Revenue:0:100",
            ],
        )

        result, output = _invoke(cli_runner, journal_cli_state, ["journal", "list"])

        assert result.exit_code == 0
        assert "1" in output

    def test_shows_empty_state_when_no_entries(
        self, cli_runner: CliRunner, journal_cli_state: CliState
    ):
        result, output = _invoke(cli_runner, journal_cli_state, ["journal", "list"])

        assert result.exit_code == 0
        assert "No journal entries found." in output
