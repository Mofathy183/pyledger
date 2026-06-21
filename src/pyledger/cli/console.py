"""
Centralized Rich console configuration for PyLedger.

This module defines the visual presentation layer used throughout the
CLI application. It provides a shared console instance, reusable themes,
and enhanced traceback rendering.

Accounting-specific styles are included to visually distinguish concepts
such as debits, credits, assets, liabilities, and journal entries,
improving readability during bookkeeping workflows.
"""

from rich.console import Console
from rich.theme import Theme
from rich.traceback import install

from pyledger.cli.theme.styles import THEME_MAP, ConsoleThemes

install(
    theme=THEME_MAP[ConsoleThemes.ERROR.name.lower()],
    show_locals=True,
)

console = Console(
    theme=Theme(THEME_MAP),
    highlight=True,
    soft_wrap=True,
)
