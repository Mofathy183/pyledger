"""
Centralized Rich console configuration for PyLedger.

This module defines the visual presentation layer used throughout the
CLI application. It provides a shared console instance, reusable themes,
and enhanced traceback rendering.

Accounting-specific styles are included to visually distinguish concepts
such as debits, credits, assets, liabilities, and journal entries,
improving readability during bookkeeping workflows.
"""

import os
import sys
from enum import Enum

from rich.console import Console
from rich.theme import Theme
from rich.traceback import install


def _detect_color_level() -> str:
    """Determine whether enhanced background colors should be enabled.

    Different terminals expose different environment variables to signal
    support for true-color rendering. This helper attempts to detect
    modern terminal environments and enables background styling when
    supported.

    Returns:
        A Rich style fragment used to apply a background color when
        true-color support is available. Returns an empty string when
        enhanced styling should not be applied.
    """
    colorterm = os.environ.get("COLORTERM", "").lower()
    if colorterm in ("truecolor", "24bit"):
        return " on #EDE9E6"

    if os.environ.get("WT_SESSION"):
        return " on #EDE9E6"

    if os.environ.get("TERM_PROGRAM"):
        return " on #EDE9E6"

    if os.environ.get("PYCHARM_HOSTED") == "1":
        return " on #EDE9E6"

    term = os.environ.get("TERM", "")
    if "256color" in term:
        return " on #EDE9E6"

    if os.environ.get("PSModulePath"):
        return " on #EDE9E6"

    if sys.platform == "win32" and not os.environ.get("CONEMUANSI"):
        return ""

    return ""


_BG = _detect_color_level()


class ConsoleThemes(Enum):
    """Visual styles used throughout the PyLedger CLI.

    These themes provide a consistent visual language across the
    application.

    Categories include:

    - User interaction states:
        - Success
        - Error
        - Warning
        - Information

    - Accounting concepts:
        - Debit balances
        - Credit balances
        - Account classifications

    - Accounting reports and views:
        - Journal entries
        - T-accounts

    Enum values are Rich style definitions that are later converted
    into a Rich Theme instance.
    """

    SUCCESS = f"bold green{_BG}"
    ERROR = f"bold red{_BG}"
    WARNING = f"italic #7a6200{_BG}"
    INFO = f"italic #0f5a72{_BG}"

    DEBIT = f"bold #5C4F4A{_BG}"
    CREDIT = f"bold #8B6914{_BG}"

    ASSETS = f"bold #547A95{_BG}"
    LIABILITIES = f"bold #2a7a6e{_BG}"
    EQUITY = f"bold #744577{_BG}"

    JOURNAL_ENTRIES = f"bold #5E0006{_BG}"
    T_ACCOUNT = f"bold #462C7D{_BG}"


THEME_MAP = {theme.name.lower(): theme.value for theme in ConsoleThemes}

install(
    theme=THEME_MAP[ConsoleThemes.ERROR.name.lower()],
    show_locals=True,
)

console = Console(
    theme=Theme(THEME_MAP),
    highlight=True,
    soft_wrap=True,
)
