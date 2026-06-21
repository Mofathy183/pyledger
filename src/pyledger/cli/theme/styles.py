"""
Visual style definitions for the PyLedger CLI.

Defines the ConsoleThemes enum and the theme map used to configure
the Rich console. Kept separate from console setup so styles can be
imported without instantiating a console.
"""

from enum import Enum

from .detection import _BG


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


THEME_MAP: dict[str, str] = {theme.name.lower(): theme.value for theme in ConsoleThemes}
