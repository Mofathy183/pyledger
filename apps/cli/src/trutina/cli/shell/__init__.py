"""Public surface of the Trutina interactive shell.

`run_shell` is the only symbol anything outside this package should
import -- `trutina.cli.main` calls `from trutina.cli.shell import
run_shell` exactly as it did when this was a single module, so moving
the implementation into a package required no change on the caller's
side.
"""

from .loop import run_shell

__all__ = ["run_shell"]
