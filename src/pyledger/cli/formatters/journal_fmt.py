"""
Journal entry CLI formatting for PyLedger.

Consumes JournalViewModel and JournalLineViewModel from the journal
feature's dtos module and renders them as Rich output. This module
never imports JournalEntry or JournalLine domain schemas directly —
the ViewModel is the only contract the formatter depends on.
"""

from decimal import Decimal

from rich.console import Group
from rich.table import Table
from rich.text import Text

from pyledger.cli.console import console
from pyledger.cli.render import console_panel, console_rule, console_table
from pyledger.modules.journal.dtos import JournalLineViewModel, JournalViewModel

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _fmt_amount(amount: Decimal) -> str:
    """Format a Decimal amount for display.

    Zero amounts are rendered as an empty string so that debit and
    credit columns remain visually clean in the journal entry table.
    A line always carries exactly one non-zero amount, so the empty
    cell always falls on the side that has no posting.

    Args:
        amount: The raw Decimal value from the ViewModel.

    Returns:
        A two-decimal string such as "1,000.00", or "" for zero.
    """
    if amount == Decimal("0"):
        return ""
    return f"{amount:,.2f}"


def _is_debit_line(line: JournalLineViewModel) -> bool:
    """Determine the posting side of a journal line.

    JournalLine stores both debit_amount and credit_amount as Decimals
    defaulting to zero. The active side is the one greater than zero.

    Args:
        line: The journal line ViewModel.

    Returns:
        True when the line carries a debit posting.
    """
    return line.debit_amount > Decimal("0")


def _fmt_posting_date(vm: JournalViewModel) -> str:
    """Format the posting date for display.

    JournalEntry stores posting_date as a datetime. Only the date
    portion is relevant for display in accounting reports.

    Args:
        vm: The journal entry ViewModel.

    Returns:
        A date string in YYYY-MM-DD format.
    """
    return vm.posting_date.strftime("%Y-%m-%d")


def _build_lines_table(vm: JournalViewModel) -> Table:
    """Build the journal entry lines table.

    Each line is styled according to its posting side — debit lines
    use the debit theme, credit lines use the credit theme. This makes
    the T-account structure immediately readable in the terminal.

    Args:
        vm: The journal entry ViewModel containing the lines to render.

    Returns:
        A configured Rich Table with all journal lines added.
    """
    table = console_table(
        ("Account", "left", "assets"),
        ("Debit", "right", "debit"),
        ("Credit", "right", "credit"),
    )
    for line in vm.lines:
        is_debit = _is_debit_line(line)
        table.add_row(
            line.account,
            _fmt_amount(line.debit_amount),
            _fmt_amount(line.credit_amount),
            style="debit" if is_debit else "credit",
        )
    return table


# ---------------------------------------------------------------------------
# Public print functions
# ---------------------------------------------------------------------------


def print_journal_entry(vm: JournalViewModel) -> None:
    """Render a single journal entry as a formatted accounting panel.

    Displays the entry header, posting date, description, transaction
    lines, and debit/credit totals. The totals line is styled green
    when balanced and red when not, providing an immediate visual cue
    for accounting errors.

    Args:
        vm: The journal entry ViewModel returned by JournalService.
    """
    is_balanced = vm.total_debits == vm.total_credits
    totals_style = "success" if is_balanced else "error"

    content = Group(
        Text(f"Journal Entry  #  {vm.journal_number}", style="info"),
        Text(f"Posting Date:     {_fmt_posting_date(vm)}", style="info"),
        console_rule(),
        _build_lines_table(vm),
        console_rule(),
        Text(vm.description or "No description provided.", style="warning"),
        console_rule(),
        Text(
            f"Total Debit:   {vm.total_debits:>12,.2f}\n"
            f"Total Credit:  {vm.total_credits:>12,.2f}",
            style=totals_style,
        ),
    )

    console.print(console_panel(content, title="Journal Entry"))


def print_journal_list(entries: list[JournalViewModel]) -> None:
    """Render a summary table of multiple journal entries.

    Used by the journal list command to display an overview of all
    entries without expanding the individual line detail.

    Args:
        entries: List of JournalViewModels to display in the summary.
    """
    if not entries:
        console.print(
            console_panel(
                Text("No journal entries found.", style="warning"),
                title="Journal Entries",
                style="warning",
            )
        )
        return

    table = console_table(
        ("#", "right", "info"),
        ("Date", "left", "info"),
        ("Description", "left", "warning"),
        ("Debits", "right", "debit"),
        ("Credits", "right", "credit"),
        ("Balanced", "center", "info"),
    )

    for vm in entries:
        is_balanced = vm.total_debits == vm.total_credits
        table.add_row(
            str(vm.journal_number),
            _fmt_posting_date(vm),
            vm.description or "—",
            f"{vm.total_debits:,.2f}",
            f"{vm.total_credits:,.2f}",
            "[success]✓[/]" if is_balanced else "[error]✗[/]",
        )

    console.print(
        console_panel(
            table,
            title=f"Journal Entries  ({len(entries)} total)",
        )
    )
