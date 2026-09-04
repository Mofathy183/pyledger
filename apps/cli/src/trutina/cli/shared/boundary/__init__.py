"""Error-rendering boundary for the Trutina CLI.

Groups error_boundary.py into its own package rather than leaving it
as the one loose module directly under cli/shared/, sitting next to
errors/, formatters/, interaction/, and ui/ -- every other error-
adjacent concern in shared/ is already its own package.
error_boundary.py combines all three of those (errors/, formatters/,
ui/) into the single seam every command wraps its one state.call(...)
in, which is exactly the kind of module that deserved a package of its
own rather than looking like a stray file among directories.

Still importable from its original path
(trutina.cli.shared.error_boundary) -- that module now forwards here
rather than defining anything itself, so every existing consumer
(every feature's command.py) keeps working with zero changes.
"""

from .error_boundary import error_boundary

__all__ = ["error_boundary"]
