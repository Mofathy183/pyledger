import pytest
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from trutina.cli.features.account import formatter as account_fmt
from trutina.core.account.dtos import AccountViewModel, ChartOfAccountsViewModel
from trutina.core.account.schemas.account import AccountCategory, NormalBalance


def _account_vm(
    code: str = "1001",
    name: str = "Cash",
    category: AccountCategory = AccountCategory.ASSET,
    normal_balance: NormalBalance = "debit",
) -> AccountViewModel:
    return AccountViewModel(
        code=code,
        name=name,
        category=category,
        normal_balance=normal_balance,
    )


def _render(renderable) -> str:
    """Render through the formatter's own themed console.

    Using account_fmt.console (the same object print_*() calls) rather
    than a bare rich.console.Console means custom style names like
    "info"/"debit"/"credit" resolve correctly instead of raising a
    missing-style error.
    """
    with account_fmt.console.capture() as capture:
        account_fmt.console.print(renderable)
    return capture.get()


def _as_group(renderable) -> Group:
    """Narrow Panel.renderable to Group, asserting the shape as a side effect."""
    assert isinstance(renderable, Group)
    return renderable


def _as_text(renderable) -> Text:
    """Narrow a renderable to Text, asserting the shape as a side effect."""
    assert isinstance(renderable, Text)
    return renderable


@pytest.mark.unit
class TestBuildAccount:
    def test_returns_panel_titled_account(self):
        result = account_fmt.build_account(_account_vm())

        assert isinstance(result, Panel)
        assert result.title == "Account"

    def test_content_lines_reflect_view_model_fields(self):
        vm = _account_vm(code="1001", name="Cash", category=AccountCategory.ASSET)

        result = account_fmt.build_account(vm)
        items = list[RenderableType](_as_group(result.renderable).renderables)

        assert _as_text(items[0]).plain == "Code:     1001"
        assert _as_text(items[1]).plain == "Name:     Cash"
        assert _as_text(items[3]).plain == "Category:       ASSET"
        assert _as_text(items[4]).plain == "Normal Balance: debit"

    def test_styles_debit_normal_balance_with_debit_style(self):
        vm = _account_vm(category=AccountCategory.ASSET, normal_balance="debit")

        result = account_fmt.build_account(vm)
        items = list[RenderableType](_as_group(result.renderable).renderables)
        balance_line = _as_text(items[4])

        assert balance_line.style == "debit"

    def test_styles_credit_normal_balance_with_credit_style(self):
        vm = _account_vm(category=AccountCategory.REVENUE, normal_balance="credit")

        result = account_fmt.build_account(vm)
        items = list[RenderableType](_as_group(result.renderable).renderables)
        balance_line = _as_text(items[4])

        assert balance_line.style == "credit"


@pytest.mark.unit
class TestBuildAccountList:
    def test_returns_warning_panel_when_no_accounts(self):
        vm = ChartOfAccountsViewModel(accounts=[])

        result = account_fmt.build_account_list(vm)
        content = _as_text(result.renderable)

        assert isinstance(result, Panel)
        assert result.title == "Chart of Accounts"
        assert result.style == "warning"
        assert content.plain == "No accounts found."
        assert content.style == "warning"

    def test_title_includes_total_account_count(self):
        vm = ChartOfAccountsViewModel(
            accounts=[
                _account_vm(code="1001"),
                _account_vm(code="2001", name="Revenue"),
            ]
        )

        result = account_fmt.build_account_list(vm)

        assert result.title == "Chart of Accounts  (2 total)"

    def test_returns_panel_containing_a_table_when_accounts_exist(self):
        vm = ChartOfAccountsViewModel(accounts=[_account_vm()])

        result = account_fmt.build_account_list(vm)

        assert isinstance(result.renderable, Table)

    def test_rendered_output_includes_every_account(self):
        vm = ChartOfAccountsViewModel(
            accounts=[
                _account_vm(code="1001", name="Cash"),
                _account_vm(
                    code="2001",
                    name="Sales Revenue",
                    category=AccountCategory.REVENUE,
                    normal_balance="credit",
                ),
            ]
        )

        output = _render(account_fmt.build_account_list(vm))

        assert "1001" in output
        assert "Cash" in output
        assert "2001" in output
        assert "Sales Revenue" in output


@pytest.mark.unit
class TestBuildDeleted:
    def test_returns_success_styled_text(self):
        result = account_fmt.build_deleted("Cash")

        assert isinstance(result, Text)
        assert result.plain == 'Account "Cash" deleted.'
        assert result.style == "success"

    def test_account_name_is_never_interpreted_as_markup(self):
        result = account_fmt.build_deleted("[bold]Cash[/bold]")

        output = _render(result)

        assert "[bold]Cash[/bold]" in output


@pytest.mark.unit
class TestBuildAborted:
    def test_uses_default_message(self):
        result = account_fmt.build_aborted()

        assert result.plain == "Aborted — no changes made."
        assert result.style == "warning"

    def test_uses_custom_message_when_provided(self):
        result = account_fmt.build_aborted("Update cancelled.")

        assert result.plain == "Update cancelled."
        assert result.style == "warning"


@pytest.mark.unit
class TestPrintFunctions:
    def test_print_account_renders_the_built_panel(self):
        output = _render(account_fmt.build_account(_account_vm(code="1001")))
        with account_fmt.console.capture() as capture:
            account_fmt.print_account(_account_vm(code="1001"))

        assert capture.get() == output

    def test_print_account_list_renders_the_built_panel(self):
        vm = ChartOfAccountsViewModel(accounts=[_account_vm()])
        output = _render(account_fmt.build_account_list(vm))

        with account_fmt.console.capture() as capture:
            account_fmt.print_account_list(vm)

        assert capture.get() == output

    def test_print_deleted_renders_the_built_message(self):
        output = _render(account_fmt.build_deleted("Cash"))

        with account_fmt.console.capture() as capture:
            account_fmt.print_deleted("Cash")

        assert capture.get() == output

    def test_print_aborted_renders_the_built_message(self):
        output = _render(account_fmt.build_aborted())

        with account_fmt.console.capture() as capture:
            account_fmt.print_aborted()

        assert capture.get() == output


@pytest.mark.unit
class TestBalanceStyle:
    @pytest.mark.parametrize(
        ("category", "normal_balance", "expected"),
        [
            (AccountCategory.ASSET, "debit", "debit"),
            (AccountCategory.REVENUE, "credit", "credit"),
        ],
    )
    def test_returns_style_matching_normal_balance(
        self,
        category: AccountCategory,
        normal_balance: NormalBalance,
        expected: str,
    ):
        vm = _account_vm(
            category=category,
            normal_balance=normal_balance,
        )

        assert account_fmt._balance_style(vm) == expected


@pytest.mark.unit
class TestBuildAccountsTable:
    def test_creates_table_with_expected_columns(self):
        table = account_fmt._build_accounts_table([])

        headers = [column.header for column in table.columns]

        assert headers == [
            "Code",
            "Name",
            "Category",
            "Normal Balance",
        ]

    def test_adds_one_row_per_account(self):
        accounts = [
            _account_vm(code="1001", name="Cash"),
            _account_vm(
                code="2001",
                name="Sales Revenue",
                category=AccountCategory.REVENUE,
                normal_balance="credit",
            ),
        ]

        table = account_fmt._build_accounts_table(accounts)

        assert len(table.rows) == 2
