"""
Posting CLI formatting for PyLedger.

Consumes PostingViewModel from the posting feature's dtos module and
renders it as Rich renderables. This module never imports LedgerPosting
domain schemas directly — the ViewModel is the only contract it
depends on.

Every PostingService method returns list[PostingViewModel]
(post_journal_entry, get_postings_by_account,
get_postings_by_journal_number) — there is no single-posting output
shape anywhere in this feature, unlike Account/Journal which each have
a "get one" command. This formatter therefore only needs one build
function, reused by every posting command.

Build functions are pure: they construct and return a Rich renderable
without printing it. Print functions are thin wrappers that build then
print. Mirrors cli/features/account/formatter.py and
cli/features/journal/formatter.py exactly.
"""

from decimal import Decimal

from pyledger.cli.shared.ui import console, panel, table
from pyledger.core.posting.dtos import PostingViewModel
from rich.panel import Panel
from rich.text import Text

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _fmt_amount(amount: Decimal | None) -> str:
    """Format an optional Decimal amount for display.

    PostingViewModel carries debit_amount/credit_amount as
    Decimal | None rather than Account/Journal's zero-defaulted
    Decimal — a debit posting's credit_amount is None (not zero) and
    vice versa. None renders as an empty string so debit and credit
    columns stay visually clean, matching the empty-cell convention
    already used by journal_fmt._fmt_amount for the zero side.

    Args:
        amount: The raw Decimal value from the ViewModel, or None.

    Returns:
        A two-decimal string such as "1,000.00", or "" if amount is None.
    """
    if amount is None:
        return ""
    return f"{amount:,.2f}"


def _fmt_posting_date(vm: PostingViewModel) -> str:
    """Format a posting's date as YYYY-MM-DD."""
    return vm.posting_date.strftime("%Y-%m-%d")


def _build_postings_table(postings: list[PostingViewModel]):
    """Build the postings summary table.

    Each row is styled by its posting side — debit postings use the
    debit theme, credit postings use the credit theme — mirroring the
    same convention used by journal_fmt._build_lines_table.

    Args:
        postings: The posting ViewModels to render as rows.

    Returns:
        A configured Rich Table with all postings added.
    """
    built = table(
        ("Account", "left", "assets"),
        ("Debit", "right", "debit"),
        ("Credit", "right", "credit"),
        ("Journal #", "right", "info"),
        ("Date", "left", "info"),
    )
    for vm in postings:
        built.add_row(
            vm.account,
            _fmt_amount(vm.debit_amount),
            _fmt_amount(vm.credit_amount),
            str(vm.journal_number),
            _fmt_posting_date(vm),
            style="debit" if vm.is_debit else "credit",
        )
    return built


# ---------------------------------------------------------------------------
# Public build functions — pure, return a renderable, never print
# ---------------------------------------------------------------------------


def build_postings_list(postings: list[PostingViewModel], *, title: str) -> Panel:
    """Build a summary panel for a list of postings.

    Returns an explicit empty-state panel when no postings exist,
    otherwise a panel containing the postings table. The same function
    backs every posting command's output (post, get-by-account,
    get-by-journal-number) since all three return list[PostingViewModel].

    Args:
        postings: The posting ViewModels to render.
        title: Panel title — callers supply a command-specific title
            (e.g. "Postings for Journal Entry #3") since there is no
            single generic title that fits all three call sites.

    Returns:
        A configured Rich Panel. Not printed.
    """
    if not postings:
        return panel(
            Text("No postings found.", style="warning"),
            title=title,
            style="warning",
        )

    return panel(_build_postings_table(postings), title=title)


# ---------------------------------------------------------------------------
# Public print functions — thin: build, then print
# ---------------------------------------------------------------------------


def print_postings_list(postings: list[PostingViewModel], *, title: str) -> None:
    """Build and print a postings summary panel.

    Args:
        postings: The posting ViewModels to render.
        title: Panel title for this specific listing.
    """
    console.print(build_postings_list(postings, title=title))
