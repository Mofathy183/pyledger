import pytest
from rich import box
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from pyledger.cli.shared.ui import (
    panel,
    rule,
    table,
)


@pytest.mark.unit
class TestConsolePanel:
    def test_builds_panel_with_default_configuration(self):
        p = panel("Hello", title="Success")

        assert isinstance(p, Panel)
        assert p.title == "Success"
        assert p.style == "success"
        assert p.border_style == "success"
        assert p.padding == (1, 2)

    def test_builds_panel_with_custom_style(self):
        p = panel(
            "Something went wrong",
            title="Error",
            style="error",
        )

        assert p.style == "error"
        assert p.border_style == "error"


@pytest.mark.unit
class TestConsoleRule:
    def test_builds_rule_with_default_style(self):
        r = rule()

        assert isinstance(r, Rule)
        assert r.style == "success"

    def test_builds_rule_with_custom_style(self):
        r = rule(style="warning")

        assert r.style == "warning"


@pytest.mark.unit
class TestConsoleTable:
    def test_builds_table_with_expected_configuration(self):
        t = table(
            ("Account", "left", "account"),
            ("Debit", "right", "debit"),
            ("Credit", "right", "credit"),
        )

        assert isinstance(t, Table)

        assert t.box == box.SIMPLE
        assert t.expand is True
        assert len(t.columns) == 3

    def test_adds_columns_in_order(self):
        t = table(
            ("Account", "left", "account"),
            ("Debit", "right", "debit"),
            ("Credit", "right", "credit"),
        )

        account = t.columns[0]
        debit = t.columns[1]
        credit = t.columns[2]

        assert account.header == "Account"
        assert account.justify == "left"
        assert account.style == "account"

        assert debit.header == "Debit"
        assert debit.justify == "right"
        assert debit.style == "debit"

        assert credit.header == "Credit"
        assert credit.justify == "right"
        assert credit.style == "credit"

    def test_returns_empty_table_when_no_columns_are_given(self):
        t = table()

        assert isinstance(t, Table)
        assert len(t.columns) == 0
        assert t.expand is True
        assert t.box == box.SIMPLE
