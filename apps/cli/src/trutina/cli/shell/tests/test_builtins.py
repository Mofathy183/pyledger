import pytest
from trutina.cli.shell.builtins import SHELL_BUILTINS


@pytest.mark.unit
class TestShellBuiltins:
    def test_exit_terminates(self):
        assert SHELL_BUILTINS["exit"].terminates is True

    def test_help_does_not_terminate(self):
        assert SHELL_BUILTINS["help"].terminates is False

    def test_every_builtin_has_a_description(self):
        assert all(b.description for b in SHELL_BUILTINS.values())

    def test_builtin_is_frozen(self):
        builtin = SHELL_BUILTINS["help"]
        with pytest.raises(AttributeError):
            builtin.description = "changed"  # ty: ignore[invalid-assignment]
