import os
import sys


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
