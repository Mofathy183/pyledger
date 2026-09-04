"""prompt_toolkit styling for the Trutina interactive shell.

Lives alongside the rest of cli/shared/ui/ for the same reason
shell_banner.py does -- shell/loop.py owns the REPL loop, not colors.

The completion menu is styled flat and borderless -- every row keeps
the terminal's own background ("bg:default") instead of
prompt_toolkit's stock solid-color highlight block, and the
highlighted row is distinguished by weight (bold + underline) rather
than an inverted background bar. This matches the reference terminal
UX supplied for this feature (a plain, left-aligned command/description
list under the prompt) rather than a floating popup box.

Note this is *not* mechanically derived from cli/shared/ui/theme/
(styles.py): Rich style strings like "bold green" or "italic #0f5a72"
aren't a format prompt_toolkit's Style understands directly, so there
is no code-level link between the two palettes today. If
cli/shared/ui/theme/styles.py's palette changes and the shell should
follow, update _ACCENT/_META below by hand -- this is a documented
gap, not an oversight.
"""

from prompt_toolkit.styles import Style
from trutina.cli.shared.ui.theme.styles import _BrandHex

# Sourced from the same brass/warm-neutral pair the Rich-side theme
# uses for brand chrome (ConsoleThemes.BRAND / BRAND_DIM) -- see that
# module for why the literal lives there and is imported here rather
# than duplicated. Only the raw hex is shared; bold/italic/underline
# modifiers still have to be expressed separately per API, since
# prompt_toolkit's Style dict and Rich's style strings aren't
# interchangeable formats -- that gap is real and unavoidable, not
# an oversight.
_ACCENT = _BrandHex.BRAND
_META = _BrandHex.BRAND_DIM


def build_shell_style() -> Style:
    """Build the prompt_toolkit Style for the shell prompt and completion menu."""
    return Style.from_dict(
        {
            "prompt": f"{_ACCENT} bold",
            "completion-menu.completion": f"bg:default {_ACCENT}",
            "completion-menu.completion.current": (
                f"bg:default {_ACCENT} bold underline"
            ),
            "completion-menu.meta.completion": f"bg:default {_META} italic",
            "completion-menu.meta.completion.current": f"bg:default {_META} italic",
        }
    )
