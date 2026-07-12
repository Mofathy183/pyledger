"""
Account CLI formatting for PyLedger.

Consumes AccountViewModel and ChartOfAccountsViewModel from the account
feature's dtos module and renders them as Rich renderable. This module
never imports Account or ChartOfAccounts domain schemas directly — the
ViewModel is the only contract the formatter depends on.

Build functions are pure: they construct and return a Rich renderable
without printing it. Print functions are thin wrappers that build then
print. This mirrors cli/shared/formatters/error.py, where
build_error_panels() returns renderable and the caller owns printing.

All Account CLI output — including one-line status messages such as
"account deleted" or "aborted" — is built here. command.py must never
construct or print Rich markup directly; every user-facing string is
composed as a Text/Panel object in this module so presentation stays
in one place and interpolated values (account names, codes) are never
embedded in raw markup strings.
"""

from pyledger.cli.shared.ui import console, panel, rule, table
from pyledger.core.account.dtos import AccountViewModel, ChartOfAccountsViewModel
from rich.console import Group
from rich.panel import Panel
from rich.text import Text

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _balance_style(vm: AccountViewModel) -> str:
    """Resolve the theme style for an account's normal balance side.

    Mirrors the debit/credit theming used by the journal formatter, so
    debit-normal and credit-normal accounts stay visually consistent
    across both features.

    Args:
        vm: The account ViewModel.

    Returns:
        "debit" or "credit", matching the account's normal_balance.
    """
    return "debit" if vm.normal_balance == "debit" else "credit"


def _build_accounts_table(accounts: list[AccountViewModel]):
    """Build the chart-of-accounts summary table.

    Each row is styled according to the account's normal balance side,
    so debit-normal and credit-normal accounts remain visually
    distinguishable at a glance.

    Args:
        accounts: The account ViewModels to render as rows.

    Returns:
        A configured Rich Table with all accounts added.
    """
    built = table(
        ("Code", "left", "info"),
        ("Name", "left", "info"),
        ("Category", "left", "info"),
        ("Normal Balance", "center", "info"),
    )
    for vm in accounts:
        built.add_row(
            vm.code,
            vm.name,
            vm.category.value,
            vm.normal_balance,
            style=_balance_style(vm),
        )
    return built


# ---------------------------------------------------------------------------
# Public build functions — pure, return a renderable, never print
# ---------------------------------------------------------------------------


def build_account(vm: AccountViewModel) -> Panel:
    """Build a single-account panel.

    Displays the account code, name, category, and derived normal
    balance. The normal balance line is styled to match the account's
    debit or credit side.

    Args:
        vm: The account ViewModel returned by AccountService.

    Returns:
        A configured Rich Panel. Not printed.
    """
    content = Group(
        Text(f"Code:     {vm.code}", style="info"),
        Text(f"Name:     {vm.name}", style="info"),
        rule(),
        Text(f"Category:       {vm.category.value}", style="info"),
        Text(
            f"Normal Balance: {vm.normal_balance}",
            style=_balance_style(vm),
        ),
    )

    return panel(content, title="Account")


def build_account_list(vm: ChartOfAccountsViewModel) -> Panel:
    """Build a summary panel for the full chart of accounts.

    Returns an explicit empty-state panel when no accounts exist,
    otherwise a panel containing the accounts table.

    Args:
        vm: The chart-of-accounts ViewModel to render.

    Returns:
        A configured Rich Panel. Not printed.
    """
    if not vm.accounts:
        return panel(
            Text("No accounts found.", style="warning"),
            title="Chart of Accounts",
            style="warning",
        )

    return panel(
        _build_accounts_table(vm.accounts),
        title=f"Chart of Accounts  ({len(vm.accounts)} total)",
    )


def build_deleted(name: str) -> Text:
    """Build the confirmation message shown after a successful deletion.

    Composed as a Text object rather than an interpolated markup
    string, so the account name can never be misinterpreted as Rich
    markup regardless of its content.

    Args:
        name: Display name of the account that was deleted.

    Returns:
        A styled Text renderable. Not printed.
    """
    return Text(f'Account "{name}" deleted.', style="success")


def build_aborted(message: str = "Aborted — no changes made.") -> Text:
    """Build a cancellation/no-op status message.

    Args:
        message: The status text to display. Defaults to the standard
            "no changes made" wording used when a user declines a
            confirmation prompt.

    Returns:
        A styled Text renderable. Not printed.
    """
    return Text(message, style="warning")


# ---------------------------------------------------------------------------
# Public print functions — thin: build, then print
# ---------------------------------------------------------------------------


def print_account(vm: AccountViewModel) -> None:
    """Build and print a single-account panel.

    Args:
        vm: The account ViewModel returned by AccountService.
    """
    console.print(build_account(vm))


def print_account_list(vm: ChartOfAccountsViewModel) -> None:
    """Build and print the chart-of-accounts summary panel.

    Args:
        vm: The chart-of-accounts ViewModel to render.
    """
    console.print(build_account_list(vm))


def print_deleted(name: str) -> None:
    """Build and print the post-deletion confirmation message.

    Args:
        name: Display name of the account that was deleted.
    """
    console.print(build_deleted(name))


def print_aborted(message: str = "Aborted — no changes made.") -> None:
    """Build and print a cancellation/no-op status message.

    Args:
        message: The status text to display.
    """
    console.print(build_aborted(message))
