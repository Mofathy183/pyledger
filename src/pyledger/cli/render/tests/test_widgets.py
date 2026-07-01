import pytest
from rich import box
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from pyledger.cli.render.widgets import (
    console_panel,
    console_rule,
    console_table,
)


@pytest.mark.unit
class TestConsolePanel:
    def test_builds_panel_with_default_configuration(self):
        panel = console_panel("Hello", title="Success")

        assert isinstance(panel, Panel)
        assert panel.title == "Success"
        assert panel.style == "success"
        assert panel.border_style == "success"
        assert panel.padding == (1, 2)

    def test_builds_panel_with_custom_style(self):
        panel = console_panel(
            "Something went wrong",
            title="Error",
            style="error",
        )

        assert panel.style == "error"
        assert panel.border_style == "error"


@pytest.mark.unit
class TestConsoleRule:
    def test_builds_rule_with_default_style(self):
        rule = console_rule()

        assert isinstance(rule, Rule)
        assert rule.style == "success"

    def test_builds_rule_with_custom_style(self):
        rule = console_rule(style="warning")

        assert rule.style == "warning"


@pytest.mark.unit
class TestConsoleTable:
    def test_builds_table_with_expected_configuration(self):
        table = console_table(
            ("Account", "left", "account"),
            ("Debit", "right", "debit"),
            ("Credit", "right", "credit"),
        )

        assert isinstance(table, Table)

        assert table.box == box.SIMPLE
        assert table.expand is True
        assert len(table.columns) == 3

    def test_adds_columns_in_order(self):
        table = console_table(
            ("Account", "left", "account"),
            ("Debit", "right", "debit"),
            ("Credit", "right", "credit"),
        )

        account = table.columns[0]
        debit = table.columns[1]
        credit = table.columns[2]

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
        table = console_table()

        assert isinstance(table, Table)
        assert len(table.columns) == 0
        assert table.expand is True
        assert table.box == box.SIMPLE
