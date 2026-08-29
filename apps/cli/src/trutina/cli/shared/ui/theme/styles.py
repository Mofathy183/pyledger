"""
Visual style definitions for the Trutina CLI.

Defines the ConsoleThemes enum and the theme map used to configure
the Rich console. Kept separate from console setup so styles can be
imported without instantiating a console.
"""

from enum import Enum

from .detection import BG_COLOR


class ConsoleThemes(Enum):
    """Visual styles used throughout the Trutina CLI.

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

    SUCCESS = f"bold green{BG_COLOR}"
    ERROR = f"bold red{BG_COLOR}"
    WARNING = f"italic #7a6200{BG_COLOR}"
    INFO = f"italic #0f5a72{BG_COLOR}"

    DEBIT = f"bold #5C4F4A{BG_COLOR}"
    CREDIT = f"bold #8B6914{BG_COLOR}"

    ASSETS = f"bold #547A95{BG_COLOR}"
    LIABILITIES = f"bold #2a7a6e{BG_COLOR}"
    EQUITY = f"bold #744577{BG_COLOR}"

    JOURNAL_ENTRIES = f"bold #5E0006{BG_COLOR}"
    T_ACCOUNT = f"bold #462C7D{BG_COLOR}"


THEME_MAP: dict[str, str] = {theme.name.lower(): theme.value for theme in ConsoleThemes}
