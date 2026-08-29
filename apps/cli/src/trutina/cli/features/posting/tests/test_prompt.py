import pytest
from trutina.cli.features.posting import prompt as prompt_module
from trutina.cli.features.posting.prompt import (
    prompt_account_identifier,
    prompt_journal_number,
)


@pytest.mark.unit
class TestPromptJournalNumber:
    def test_returns_parsed_int_on_valid_input(self, monkeypatch):
        monkeypatch.setattr(prompt_module, "ask", lambda *a, **k: "3")

        result = prompt_journal_number()

        assert result == 3

    def test_passes_expected_message_to_ask(self, monkeypatch):
        captured = {}

        def fake_ask(message, **kwargs):
            captured["message"] = message
            return "1"

        monkeypatch.setattr(prompt_module, "ask", fake_ask)

        prompt_journal_number()

        assert captured["message"] == "Journal Number"

    def test_reprompts_and_warns_on_invalid_input_then_succeeds(
        self, monkeypatch, capsys
    ):
        responses = iter(["abc", "5"])
        monkeypatch.setattr(prompt_module, "ask", lambda *a, **k: next(responses))

        result = prompt_journal_number()

        assert result == 5

    def test_warning_message_mentions_invalid_value(self, monkeypatch):
        from trutina.cli.shared.ui import console

        responses = iter(["xyz", "9"])
        monkeypatch.setattr(prompt_module, "ask", lambda *a, **k: next(responses))

        with console.capture() as capture:
            result = prompt_journal_number()

        assert result == 9
        assert "xyz" in capture.get()


@pytest.mark.unit
class TestPromptAccountIdentifier:
    def test_returns_cleaned_identifier(self, monkeypatch):
        monkeypatch.setattr(prompt_module, "ask", lambda *a, **k: "  Cash  ")

        result = prompt_account_identifier()

        assert result == "Cash"

    def test_passes_expected_message_to_ask(self, monkeypatch):
        captured = {}

        def fake_ask(message, **kwargs):
            captured["message"] = message
            return "Cash"

        monkeypatch.setattr(prompt_module, "ask", fake_ask)

        prompt_account_identifier()

        assert captured["message"] == "Account name"
