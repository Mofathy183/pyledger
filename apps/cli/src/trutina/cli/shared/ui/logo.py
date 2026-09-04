"""ASCII rendition of the Trutina balance-scale logo.

Redraws the same composition as trutina_logo_concept.svg -- a single
suspension point, a symmetric beam, two hanging pans, and a
triangular stand -- in box-drawing characters so it renders
identically across the terminals this CLI actually runs in. There is
no code path that generates this from the SVG; if the SVG concept
changes, this rendition has to be updated by hand (the same kind of
gap shell_style.py's own docstring already flags for its color
palette).

Kept as its own module, separate from shell_banner.py, so a future
consumer (e.g. a `--version` flag) can reuse just the mark without
pulling in the rest of the welcome banner's copy.
"""

from rich.console import Group
from rich.text import Text

_MARK_LINES = [
    "        ●        ",
    "   ┌────┴────┐   ",
    " (○)         (○) ",
    "       ╱ ╲       ",
    "      ╱   ╲      ",
    "     ╱     ╲     ",
    "     ▔▔▔▔▔▔▔     ",
]


def build_logo(*, style: str = "brand") -> Group:
    """Build the ASCII balance-scale mark plus the Trutina wordmark.

    Args:
        style: Theme name applied to the scale's line art and wordmark.
            Defaults to "brand" -- a color deliberately not reused from
            any operational theme (success/error/journal_entries/etc.),
            so the static logo can never be misread as a status signal.

    Returns:
        A Rich Group: the scale glyph, the letter-spaced "TRUTINA"
        wordmark, and the tagline from the original logo concept.
    """
    mark = Text("\n".join(_MARK_LINES), style=style, justify="center")
    wordmark = Text("T R U T I N A", style=style, justify="center")
    tagline = Text("double-entry, in balance", style="brand_dim", justify="center")

    return Group(mark, Text(""), wordmark, tagline)
