"""
Journal CLI formatting for PyLedger.

Consumes JournalViewModel and JournalLineViewModel from the journal
feature's dtos module and renders them as Rich renderables. This module
never imports JournalEntry or JournalLine domain schemas directly — the
ViewModel is the only contract it depends on.

Build functions are pure: they construct and return a Rich renderable
without printing it. Print functions are thin wrappers that build then
print. Mirrors cli/features/account/formatter.py exactly.
"""

from decimal import Decimal

from pyledger.cli.shared.ui import console, panel, rule, table
from pyledger.core.journal.dtos import JournalLineViewModel, JournalViewModel
from rich.console import Group
from rich.panel import Panel
from rich.text import Text

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _fmt_amount(amount: Decimal) -> str:
    """Format a Decimal amount for display.

    Zero amounts render as an empty string so debit and credit columns
    stay visually clean — a line always carries exactly one non-zero
    amount, so the empty cell always falls on the side with no posting.
    """
    if amount == Decimal("0"):
        return ""
    return f"{amount:,.2f}"


def _is_debit_line(line: JournalLineViewModel) -> bool:
    """Return True when a journal line records a debit posting."""
    return line.debit_amount > Decimal("0")


def _fmt_posting_date(vm: JournalViewModel) -> str:
    """Format a journal entry's posting date as YYYY-MM-DD."""
    return vm.posting_date.strftime("%Y-%m-%d")


def _build_lines_table(vm: JournalViewModel):
    """Build the journal entry lines table.

    Each line is styled by its posting side — debit lines use the
    debit theme, credit lines use the credit theme — so the T-account
    structure reads clearly in the terminal.
    """
    built = table(
        ("Account", "left", "assets"),
        ("Debit", "right", "debit"),
        ("Credit", "right", "credit"),
    )
    for line in vm.lines:
        is_debit = _is_debit_line(line)
        built.add_row(
            line.account,
            _fmt_amount(line.debit_amount),
            _fmt_amount(line.credit_amount),
            style="debit" if is_debit else "credit",
        )
    return built


def _build_journal_summary_table(entries: list[JournalViewModel]):
    """Build the multi-entry summary table used by the list command."""
    built = table(
        ("#", "right", "info"),
        ("Date", "left", "info"),
        ("Description", "left", "warning"),
        ("Debits", "right", "debit"),
        ("Credits", "right", "credit"),
        ("Balanced", "center", "info"),
    )
    for vm in entries:
        built.add_row(
            str(vm.journal_number),
            _fmt_posting_date(vm),
            vm.description or "—",
            f"{vm.total_debits:,.2f}",
            f"{vm.total_credits:,.2f}",
            "[success]✓[/]" if vm.is_balanced else "[error]✗[/]",
        )
    return built


# ---------------------------------------------------------------------------
# Public build functions — pure, return a renderable, never print
# ---------------------------------------------------------------------------


def build_journal_entry(vm: JournalViewModel) -> Panel:
    """Build a single journal-entry panel.

    Displays the entry header, posting date, lines, description, and
    debit/credit totals. The totals line is styled "success" when
    balanced and "error" otherwise — JournalEntry's domain invariant
    guarantees this is always "success" for anything JournalService
    returns, but the styling stays defensive.

    Args:
        vm: The journal entry ViewModel returned by JournalService.

    Returns:
        A configured Rich Panel. Not printed.
    """
    totals_style = "success" if vm.is_balanced else "error"

    content = Group(
        Text(f"Journal Entry  #  {vm.journal_number}", style="info"),
        Text(f"Posting Date:     {_fmt_posting_date(vm)}", style="info"),
        rule(),
        _build_lines_table(vm),
        rule(),
        Text(vm.description or "No description provided.", style="warning"),
        rule(),
        Text(
            f"Total Debit:   {vm.total_debits:>12,.2f}\n"
            f"Total Credit:  {vm.total_credits:>12,.2f}",
            style=totals_style,
        ),
    )

    return panel(content, title="Journal Entry")


def build_journal_list(entries: list[JournalViewModel]) -> Panel:
    """Build a summary panel for multiple journal entries.

    Returns an explicit empty-state panel when no entries exist,
    otherwise a panel containing the summary table.

    Args:
        entries: The journal entry ViewModels to render as rows.

    Returns:
        A configured Rich Panel. Not printed.
    """
    if not entries:
        return panel(
            Text("No journal entries found.", style="warning"),
            title="Journal Entries",
            style="warning",
        )

    return panel(
        _build_journal_summary_table(entries),
        title=f"Journal Entries  ({len(entries)} total)",
    )


# ---------------------------------------------------------------------------
# Public print functions — thin: build, then print
# ---------------------------------------------------------------------------


def print_journal_entry(vm: JournalViewModel) -> None:
    """Build and print a single journal-entry panel.

    Args:
        vm: The journal entry ViewModel returned by JournalService.
    """
    console.print(build_journal_entry(vm))


def print_journal_list(entries: list[JournalViewModel]) -> None:
    """Build and print the journal-entries summary panel.

    Args:
        entries: The journal entry ViewModels to render.
    """
    console.print(build_journal_list(entries))
