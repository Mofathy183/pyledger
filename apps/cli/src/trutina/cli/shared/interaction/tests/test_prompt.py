from unittest.mock import MagicMock

import pytest
from trutina.cli.shared.interaction import prompt


@pytest.mark.unit
class TestAsk:
    def test_returns_typed_value(self, monkeypatch):
        monkeypatch.setattr(
            prompt.Prompt,
            "ask",
            staticmethod(lambda *args, **kwargs: "typed value"),
        )

        result = prompt.ask("Account Code")

        assert result == "typed value"

    def test_passes_default_through_when_provided(self, monkeypatch):
        captured = {}

        def fake_ask(prompt_text, *, default=None, console=None):
            captured["prompt_text"] = prompt_text
            captured["default"] = default
            captured["console"] = console
            return default

        monkeypatch.setattr(prompt.Prompt, "ask", staticmethod(fake_ask))

        result = prompt.ask("Account Name", default="Cash")

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

        prompt.ask("Account Code")

        assert captured["had_default"] is False

    def test_wraps_message_in_requested_style(self, monkeypatch):
        captured = {}

        def fake_ask(prompt_text, *, console=None, **kwargs):
            captured["prompt_text"] = prompt_text
            return "value"

        monkeypatch.setattr(prompt.Prompt, "ask", staticmethod(fake_ask))

        prompt.ask("Account Code", style="warning")

        assert captured["prompt_text"] == "[warning]Account Code[/]"


@pytest.mark.unit
class TestConfirm:
    def test_returns_true_when_confirmed(self, monkeypatch):
        monkeypatch.setattr(
            prompt.Confirm,
            "ask",
            staticmethod(lambda *args, **kwargs: True),
        )

        assert prompt.confirm("Proceed?") is True

    def test_returns_false_when_declined(self, monkeypatch):
        monkeypatch.setattr(
            prompt.Confirm,
            "ask",
            staticmethod(lambda *args, **kwargs: False),
        )

        assert prompt.confirm("Proceed?") is False

    def test_passes_default_and_style_through(self, monkeypatch):
        captured = {}

        def fake_ask(prompt_text, *, default, console):
            captured["prompt_text"] = prompt_text
            captured["default"] = default
            captured["console"] = console
            return default

        monkeypatch.setattr(prompt.Confirm, "ask", staticmethod(fake_ask))

        prompt.confirm("Proceed?", default=True, style="error")

        assert captured["default"] is True
        assert captured["console"] is prompt.console
        assert captured["prompt_text"] == "[error]Proceed?[/]"


@pytest.mark.unit
class TestSelect:
    def test_returns_selected_option_by_index(self, monkeypatch):
        monkeypatch.setattr(prompt.console, "print", MagicMock())
        monkeypatch.setattr(prompt, "panel", MagicMock(return_value="panel"))
        monkeypatch.setattr(prompt, "rule", MagicMock(return_value="rule"))

        monkeypatch.setattr(
            prompt.Prompt,
            "ask",
            staticmethod(lambda *args, **kwargs: "2"),
        )

        result = prompt.select("Pick one", ["a", "b", "c"])

        assert result == "b"

    def test_uses_default_option_when_provided(self, monkeypatch):
        monkeypatch.setattr(prompt.console, "print", MagicMock())
        monkeypatch.setattr(prompt, "panel", MagicMock(return_value="panel"))
        monkeypatch.setattr(prompt, "rule", MagicMock(return_value="rule"))

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

        result = prompt.select("Pick one", ["a", "b", "c"], default="c")

        assert result == "c"
        assert captured["prompt_text"] == "[info]Enter a number[/]"
        assert captured["choices"] == ["1", "2", "3"]
        assert captured["default"] == "3"
        assert captured["show_choices"] is False
        assert captured["console"] is prompt.console

    def test_omits_default_kwarg_when_none(self, monkeypatch):
        monkeypatch.setattr(prompt.console, "print", MagicMock())
        monkeypatch.setattr(prompt, "panel", MagicMock(return_value="panel"))
        monkeypatch.setattr(prompt, "rule", MagicMock(return_value="rule"))

        captured = {}

        def fake_ask(
            prompt_text,
            *,
            choices,
            show_choices,
            console,
            **kwargs,
        ):
            captured["had_default"] = "default" in kwargs
            return "1"

        monkeypatch.setattr(prompt.Prompt, "ask", staticmethod(fake_ask))

        prompt.select("Pick one", ["a", "b"])

        assert captured["had_default"] is False

    def test_renders_selection_panel_before_prompting(self, monkeypatch):
        printed = MagicMock()
        panel_mock = MagicMock(return_value="panel")
        rule_mock = MagicMock(return_value="rule")

        monkeypatch.setattr(prompt.console, "print", printed)
        monkeypatch.setattr(prompt, "panel", panel_mock)
        monkeypatch.setattr(prompt, "rule", rule_mock)

        monkeypatch.setattr(
            prompt.Prompt,
            "ask",
            staticmethod(lambda *args, **kwargs: "1"),
        )

        prompt.select("Pick one", ["a", "b"])

        rule_mock.assert_called_once_with(style="info")
        panel_mock.assert_called_once()
        printed.assert_called_once_with("panel")

    def test_passes_custom_title_to_panel(self, monkeypatch):
        monkeypatch.setattr(prompt.console, "print", MagicMock())
        monkeypatch.setattr(prompt, "rule", MagicMock(return_value="rule"))

        panel_mock = MagicMock(return_value="panel")
        monkeypatch.setattr(prompt, "panel", panel_mock)

        monkeypatch.setattr(
            prompt.Prompt,
            "ask",
            staticmethod(lambda *args, **kwargs: "1"),
        )

        prompt.select(
            "Pick one",
            ["a", "b"],
            title="Accounts",
        )

        assert panel_mock.call_args.kwargs["title"] == "Accounts"

    def test_uses_custom_label_function(self, monkeypatch):
        monkeypatch.setattr(prompt.console, "print", MagicMock())
        monkeypatch.setattr(prompt, "panel", MagicMock(return_value="panel"))
        monkeypatch.setattr(prompt, "rule", MagicMock(return_value="rule"))

        monkeypatch.setattr(
            prompt.Prompt,
            "ask",
            staticmethod(lambda *args, **kwargs: "2"),
        )

        options = [
            {"name": "Cash"},
            {"name": "Bank"},
        ]

        result = prompt.select(
            "Pick one",
            options,
            label=lambda option: option["name"],
        )

        assert result == options[1]
