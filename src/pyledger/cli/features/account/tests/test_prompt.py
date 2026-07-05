"""Unit tests for the Account CLI interactive prompt adapter.

prompt.py wraps Rich's Prompt/Confirm as its sole I/O boundary, so
every test here fakes exactly that boundary — nothing else. parser.py's
real functions run unmocked, so DTO construction is genuinely exercised
through the interactive path, not just asserted by inspection.
"""

from unittest.mock import MagicMock

import pytest
from rich.panel import Panel

from pyledger.cli.features.account import prompt
from pyledger.modules.account.dtos import CreateAccountInput, UpdateAccountInput
from pyledger.modules.account.schemas.account import AccountCategory


@pytest.mark.unit
class TestAsk:
    def test_returns_typed_value(self, monkeypatch):
        monkeypatch.setattr(
            prompt.Prompt, "ask", staticmethod(lambda *a, **k: "typed value")
        )

        result = prompt._ask("Account Code")

        assert result == "typed value"

    def test_passes_default_through_when_provided(self, monkeypatch):
        captured = {}

        def fake_ask(prompt_text, *, default=None, console=None):
            captured["prompt_text"] = prompt_text
            captured["default"] = default
            captured["console"] = console
            return default

        monkeypatch.setattr(prompt.Prompt, "ask", staticmethod(fake_ask))

        result = prompt._ask("Account Name", default="Cash")

        assert result == "Cash"
        assert captured["prompt_text"] == "[info]Account Name[/]"
        assert captured["default"] == "Cash"
        assert captured["console"] is prompt.console

    def test_omits_default_kwarg_when_none(self, monkeypatch):
        captured = {}

        def fake_ask(prompt_text, *, console=None, **kwargs):
            captured["had_default"] = "default" in kwargs
            return "value"

        monkeypatch.setattr(prompt.Prompt, "ask", staticmethod(fake_ask))

        prompt._ask("Account Code")

        assert captured["had_default"] is False

    def test_wraps_message_in_requested_style(self, monkeypatch):
        captured = {}

        def fake_ask(prompt_text, *, console=None, **kwargs):
            captured["prompt_text"] = prompt_text
            return "value"

        monkeypatch.setattr(prompt.Prompt, "ask", staticmethod(fake_ask))

        prompt._ask("Account Code", style="warning")

        assert captured["prompt_text"] == "[warning]Account Code[/]"


@pytest.mark.unit
class TestConfirm:
    def test_returns_true_when_confirmed(self, monkeypatch):
        monkeypatch.setattr(prompt.Confirm, "ask", staticmethod(lambda *a, **k: True))

        assert prompt._confirm("Proceed?") is True

    def test_returns_false_when_declined(self, monkeypatch):
        monkeypatch.setattr(prompt.Confirm, "ask", staticmethod(lambda *a, **k: False))

        assert prompt._confirm("Proceed?") is False

    def test_passes_default_and_style_through(self, monkeypatch):
        captured = {}

        def fake_ask(prompt_text, *, default, console):
            captured["prompt_text"] = prompt_text
            captured["default"] = default
            return default

        monkeypatch.setattr(prompt.Confirm, "ask", staticmethod(fake_ask))

        prompt._confirm("Proceed?", default=True, style="error")

        assert captured["default"] is True
        assert captured["prompt_text"] == "[error]Proceed?[/]"


@pytest.mark.unit
class TestSelect:
    def test_returns_selected_option_by_index(self, monkeypatch):
        monkeypatch.setattr(prompt.console, "print", MagicMock())
        monkeypatch.setattr(prompt.Prompt, "ask", staticmethod(lambda *a, **k: "2"))

        result = prompt._select("Pick one", ["a", "b", "c"])

        assert result == "b"

    def test_uses_default_option_when_provided(self, monkeypatch):
        monkeypatch.setattr(prompt.console, "print", MagicMock())

        captured = {}

        def fake_ask(
            prompt_text,
            *,
            choices,
            default=None,
            show_choices,
            console,
        ):
            captured["prompt_text"] = prompt_text
            captured["choices"] = choices
            captured["default"] = default
            captured["show_choices"] = show_choices
            captured["console"] = console
            return default

        monkeypatch.setattr(prompt.Prompt, "ask", staticmethod(fake_ask))

        result = prompt._select("Pick one", ["a", "b", "c"], default="c")

        assert result == "c"
        assert captured["prompt_text"] == "[info]Enter a number[/]"
        assert captured["choices"] == ["1", "2", "3"]
        assert captured["default"] == "3"
        assert captured["show_choices"] is False
        assert captured["console"] is prompt.console

    def test_omits_default_kwarg_when_none(self, monkeypatch):
        monkeypatch.setattr(prompt.console, "print", MagicMock())
        captured = {}

        def fake_ask(prompt_text, *, choices, show_choices, console, **kwargs):
            captured["had_default"] = "default" in kwargs
            return "1"

        monkeypatch.setattr(prompt.Prompt, "ask", staticmethod(fake_ask))

        prompt._select("Pick one", ["a", "b"])

        assert captured["had_default"] is False

    def test_renders_selection_panel_before_prompting(self, monkeypatch):
        printed = MagicMock()

        monkeypatch.setattr(prompt.console, "print", printed)
        monkeypatch.setattr(prompt.Prompt, "ask", staticmethod(lambda *a, **k: "1"))

        prompt._select("Pick one", ["a", "b"])

        printed.assert_called_once()

        panel = printed.call_args.args[0]

        assert isinstance(panel, Panel)
        assert panel.title == "Select an Option"


@pytest.mark.unit
class TestPromptCategory:
    def test_returns_raw_string_not_enum_member(self, monkeypatch):
        monkeypatch.setattr(prompt.console, "print", MagicMock())
        monkeypatch.setattr(prompt.Prompt, "ask", staticmethod(lambda *a, **k: "1"))

        result = prompt._prompt_category()

        assert result == AccountCategory.ASSET.value
        assert isinstance(result, str)

    def test_preselects_default_category(self, monkeypatch):
        monkeypatch.setattr(prompt.console, "print", MagicMock())

        def fake_ask(prompt_text, *, choices, default=None, show_choices, console):
            return default

        monkeypatch.setattr(prompt.Prompt, "ask", staticmethod(fake_ask))

        result = prompt._prompt_category(default=AccountCategory.REVENUE)

        assert result == AccountCategory.REVENUE.value

    def test_omits_default_when_none(self, monkeypatch):
        monkeypatch.setattr(prompt.console, "print", MagicMock())
        captured = {}

        def fake_ask(prompt_text, *, choices, show_choices, console, **kwargs):
            captured["had_default"] = "default" in kwargs
            return "1"

        monkeypatch.setattr(prompt.Prompt, "ask", staticmethod(fake_ask))

        prompt._prompt_category()

        assert captured["had_default"] is False


@pytest.mark.unit
class TestPromptCreateAccount:
    def test_builds_create_account_input_from_collected_values(self, monkeypatch):
        monkeypatch.setattr(prompt.console, "print", MagicMock())

        responses = iter(["1001", "Cash", "1"])  # code, name, category (ASSET)
        monkeypatch.setattr(
            prompt.Prompt, "ask", staticmethod(lambda *a, **k: next(responses))
        )

        result = prompt.prompt_create_account()

        assert isinstance(result, CreateAccountInput)
        assert result.code == "1001"
        assert result.name == "Cash"
        assert result.category is AccountCategory.ASSET


@pytest.mark.unit
class TestPromptUpdateAccount:
    def test_builds_update_account_input_preserving_code(self, monkeypatch):
        monkeypatch.setattr(prompt.console, "print", MagicMock())

        responses = iter(["Main Cash", "5"])  # name, category (REVENUE)
        monkeypatch.setattr(
            prompt.Prompt, "ask", staticmethod(lambda *a, **k: next(responses))
        )

        result = prompt.prompt_update_account(
            current_code="1001",
            current_name="Cash",
            current_category=AccountCategory.ASSET,
        )

        assert isinstance(result, UpdateAccountInput)
        assert result.code == "1001"
        assert result.name == "Main Cash"
        assert result.category is AccountCategory.REVENUE

    def test_reusing_defaults_preserves_current_values(self, monkeypatch):
        monkeypatch.setattr(prompt.console, "print", MagicMock())

        def fake_ask(prompt_text, *, default=None, console=None, **kwargs):
            return default

        monkeypatch.setattr(prompt.Prompt, "ask", staticmethod(fake_ask))

        result = prompt.prompt_update_account(
            current_code="1001",
            current_name="Cash",
            current_category=AccountCategory.ASSET,
        )

        assert result.code == "1001"
        assert result.name == "Cash"
        assert result.category is AccountCategory.ASSET


@pytest.mark.unit
class TestPromptAccountIdentifier:
    def test_returns_raw_identifier_as_typed(self, monkeypatch):
        monkeypatch.setattr(prompt.Prompt, "ask", staticmethod(lambda *a, **k: "1001"))

        assert prompt.prompt_account_identifier() == "1001"


@pytest.mark.unit
class TestConfirmAccountDeletion:
    def test_returns_true_when_confirmed(self, monkeypatch):
        monkeypatch.setattr(prompt.Confirm, "ask", staticmethod(lambda *a, **k: True))

        assert prompt.confirm_account_deletion("Cash") is True

    def test_returns_false_when_declined(self, monkeypatch):
        monkeypatch.setattr(prompt.Confirm, "ask", staticmethod(lambda *a, **k: False))

        assert prompt.confirm_account_deletion("Cash") is False

    def test_uses_error_style_and_false_default(self, monkeypatch):
        captured = {}

        def fake_ask(prompt_text, *, default, console):
            captured["prompt_text"] = prompt_text
            captured["default"] = default
            return False

        monkeypatch.setattr(prompt.Confirm, "ask", staticmethod(fake_ask))

        prompt.confirm_account_deletion("Cash")

        assert captured["default"] is False
        assert captured["prompt_text"] == '[error]Delete account "Cash"?[/]'
