from enum import Enum

from rich.console import Console
from rich.theme import Theme
from rich.traceback import install


class ConsoleThemes(Enum):
    """
    this Themes class made to define the themes that will use in the whole the cli
    and how it will how the accounting based on the print style of it

    it will define it like that the enum will have the styling value of it
    that will use in the the theme rich

    Examples for how use itt in the Themes:
    { Themes.SUCCESS.name.lower(): Themes.SUCCESS.value }
    """

    # the actions themes that will happen in the cli
    SUCCESS = "bold green on #EDE9E6"
    ERROR = "bold red on #EDE9E6"
    WARNING = "italic yellow on #EDE9E6"
    INFO = "italic cyan on #EDE9E6"

    # the show actions themes for the accounting
    # * for the nature of the account
    DEBIT = "bold #5C4F4A on #EDE9E6"
    CREDIT = "bold #C08552 on #EDE9E6"
    # * for the type of it
    ASSETS = "bold #547A95 on #EDE9E6"
    LIABILITIES = "bold #72BAA9 on #EDE9E6"
    EQUITY = "bold #744577 on #EDE9E6"
    # * and for the where it show
    JOURNAL_ENTRIES = "bold #5E0006 on #EDE9E6"
    T_ACCOUNT = "bold #462C7D on #EDE9E6"


# walk through all the enum themes to make the dict
THEME_MAP = {theme.name.lower(): theme.value for theme in ConsoleThemes}

# for the error when surprise break happen, to use the same Error style
install(theme=THEME_MAP[ConsoleThemes.ERROR.name.lower()])

console = Console(theme=Theme(THEME_MAP))
