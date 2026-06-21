"""
Shared Rich rendering helpers used across feature formatters.

These helpers produce consistent panels, rules, and table structures
without duplicating Rich configuration in every formatter module.
Every formatter in cli/formatters/ builds its Rich output through
these three functions — no formatter constructs Panel, Rule, or Table
directly.
"""

from typing import Literal

from rich import box
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

type Justify = Literal[
    "default",
    "left",
    "center",
    "right",
    "full",
]


def console_panel(content, title: str, style: str = "success") -> Panel:
    """Build a standard PyLedger panel.

    Args:
        content: Renderable content — a Rich Group, Table, or Text.
        title: Panel title shown in the border.
        style: Theme name applied to both panel text and border.

    Returns:
        A configured Rich Panel.
    """
    return Panel(
        content,
        title=title,
        style=style,
        border_style=style,
        padding=(1, 2),
    )


def console_rule(style: str = "success") -> Rule:
    """Build a standard horizontal divider for panel sections.

    Args:
        style: Theme name applied to the rule.

    Returns:
        A configured Rich Rule.
    """
    return Rule(style=style)


def console_table(*columns: tuple[str, Justify, str]) -> Table:
    """Create a standard accounting table.

    Args:
        columns: Tuples of (header, justify, style) for each column.

    Returns:
        A configured Rich Table with all columns added, ready for
        add_row() calls.
    """
    table = Table(
        box=box.SIMPLE,
        border_style="journal_entries",
        header_style="journal_entries",
        expand=True,
    )

    for header, justify, style in columns:
        table.add_column(header, justify=justify, style=style)
    return table
