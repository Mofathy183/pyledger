import pytest
from pyledger.cli.features.journal import prompt
from pyledger.core.journal.dtos import CreateJournalInput, JournalLineInput


@pytest.mark.unit
class TestPromptPostingDate:
    def test_returns_none_when_blank(self, monkeypatch):
        monkeypatch.setattr(prompt, "ask", lambda *a, **k: "")

        assert prompt._prompt_posting_date() is None

    def test_returns_raw_value_when_provided(self, monkeypatch):
        monkeypatch.setattr(prompt, "ask", lambda *a, **k: "2024-06-15")

        assert prompt._prompt_posting_date() == "2024-06-15"

    def test_passes_blank_default_to_ask(self, monkeypatch):
        captured = {}

        def fake_ask(message, **kwargs):
            captured["message"] = message
            captured["kwargs"] = kwargs
            return ""

        monkeypatch.setattr(prompt, "ask", fake_ask)

        prompt._prompt_posting_date()

        assert captured["kwargs"]["default"] == ""


@pytest.mark.unit
class TestPromptDescription:
    def test_returns_none_when_blank(self, monkeypatch):
        monkeypatch.setattr(prompt, "ask", lambda *a, **k: "")

        assert prompt._prompt_description() is None

    def test_returns_raw_value_when_provided(self, monkeypatch):
        monkeypatch.setattr(prompt, "ask", lambda *a, **k: "Opening balance")

        assert prompt._prompt_description() == "Opening balance"


@pytest.mark.unit
class TestPromptLine:
    def test_builds_journal_line_input_from_collected_values(self, monkeypatch):
        responses = iter(["Cash", "100", "0"])
        monkeypatch.setattr(prompt, "ask", lambda *a, **k: next(responses))

        result = prompt._prompt_line(1)

        assert isinstance(result, JournalLineInput)
        assert result.account == "Cash"
        assert result.debit_amount == 100
        assert result.credit_amount == 0

    def test_labels_prompts_with_the_given_line_index(self, monkeypatch):
        captured_messages = []

        def fake_ask(message, **kwargs):
            captured_messages.append(message)
            return "Cash" if "Account" in message else "0"

        monkeypatch.setattr(prompt, "ask", fake_ask)

        prompt._prompt_line(2)

        assert captured_messages[0] == "Line 2 — Account"
        assert captured_messages[1] == "Line 2 — Debit Amount"
        assert captured_messages[2] == "Line 2 — Credit Amount"


@pytest.mark.unit
class TestPromptLines:
    def test_collects_exactly_two_lines_when_user_declines_more(self, monkeypatch):
        account_responses = iter(["Cash", "Sales Revenue"])

        def fake_ask(message, **kwargs):
            if "Account" in message:
                return next(account_responses)
            return "0"

        monkeypatch.setattr(prompt, "ask", fake_ask)
        monkeypatch.setattr(prompt, "confirm", lambda *a, **k: False)

        result = prompt._prompt_lines()

        assert len(result) == 2

    def test_collects_additional_lines_when_user_confirms(self, monkeypatch):
        accounts = iter(["Cash", "Sales Revenue", "Accounts Receivable"])

        def fake_ask(message, **kwargs):
            if "Account" in message:
                return next(accounts)
            return "0"

        monkeypatch.setattr(prompt, "ask", fake_ask)

        confirmations = iter([True, False])
        monkeypatch.setattr(prompt, "confirm", lambda *a, **k: next(confirmations))

        result = prompt._prompt_lines()

        assert len(result) == 3
        assert result[2].account == "Accounts Receivable"


@pytest.mark.unit
class TestPromptCreateJournal:
    def test_builds_create_journal_input_from_collected_values(self, monkeypatch):
        responses = iter(
            [
                "2024-06-15",  # posting date
                "Cash",  # line 1 account
                "100",  # line 1 debit
                "0",  # line 1 credit
                "Sales Revenue",  # line 2 account
                "0",  # line 2 debit
                "100",  # line 2 credit
                "Opening balance",  # description
            ]
        )
        monkeypatch.setattr(prompt, "ask", lambda *a, **k: next(responses))
        monkeypatch.setattr(prompt, "confirm", lambda *a, **k: False)

        result = prompt.prompt_create_journal()

        assert isinstance(result, CreateJournalInput)
        assert len(result.lines) == 2
        assert result.lines[0].account == "Cash"
        assert result.lines[1].account == "Sales Revenue"
        assert result.description == "Opening balance"


@pytest.mark.unit
class TestPromptJournalNumber:
    def test_returns_int_on_valid_input(self, monkeypatch):
        monkeypatch.setattr(prompt, "ask", lambda *a, **k: "42")

        assert prompt.prompt_journal_number() == 42

    def test_reprompts_and_warns_on_invalid_input(self, monkeypatch):
        responses = iter(["abc", "5"])
        monkeypatch.setattr(prompt, "ask", lambda *a, **k: next(responses))

        printed = []
        monkeypatch.setattr(
            prompt.console, "print", lambda renderable: printed.append(renderable)
        )

        result = prompt.prompt_journal_number()

        assert result == 5
        assert len(printed) == 1
        assert "abc" in printed[0].plain
        assert printed[0].style == "warning"

    def test_accepts_negative_or_zero_without_client_side_validation(self, monkeypatch):
        """prompt_journal_number() does no positivity check by design --
        it routes through JournalService's UNKNOWN_JOURNAL_ENTRY error
        path instead. See handler.py/command.py's error_boundary(); this
        test only pins the (intentional) absence of client-side rejection.
        """
        monkeypatch.setattr(prompt, "ask", lambda *a, **k: "-5")

        assert prompt.prompt_journal_number() == -5
