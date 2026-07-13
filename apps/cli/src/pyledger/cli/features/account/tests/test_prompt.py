import pytest
from pyledger.cli.features.account import prompt
from pyledger.core.account.dtos import CreateAccountInput, UpdateAccountInput
from pyledger.core.account.schemas.account import AccountCategory


@pytest.mark.unit
class TestPromptCategory:
    def test_returns_raw_string_from_selection(self, monkeypatch):
        monkeypatch.setattr(prompt, "select", lambda *a, **k: "asset")

        result = prompt._prompt_category()

        assert result == "asset"
        assert isinstance(result, str)

    def test_passes_expected_configuration_to_select(self, monkeypatch):
        captured = {}

        def fake_select(message, options, **kwargs):
            captured["message"] = message
            captured["options"] = options
            captured["kwargs"] = kwargs
            return "revenue"

        monkeypatch.setattr(prompt, "select", fake_select)

        result = prompt._prompt_category(default=AccountCategory.REVENUE)

        assert result == "revenue"

        assert captured["message"] == "Choose account category"
        assert captured["options"] == [category.value for category in AccountCategory]
        assert captured["kwargs"]["default"] == AccountCategory.REVENUE.value
        assert captured["kwargs"]["title"] == "Account Category"
        assert callable(captured["kwargs"]["label"])


@pytest.mark.unit
class TestPromptCreateAccount:
    def test_builds_create_account_input_from_collected_values(self, monkeypatch):
        responses = iter(["1001", "Cash"])

        monkeypatch.setattr(prompt, "ask", lambda *a, **k: next(responses))
        monkeypatch.setattr(prompt, "select", lambda *a, **k: "asset")

        result = prompt.prompt_create_account()

        assert isinstance(result, CreateAccountInput)
        assert result.code == "1001"
        assert result.name == "Cash"
        assert result.category is AccountCategory.ASSET


@pytest.mark.unit
class TestPromptUpdateAccount:
    def test_builds_update_account_input_preserving_code(self, monkeypatch):
        responses = iter(["Main Cash"])

        monkeypatch.setattr(prompt, "ask", lambda *a, **k: next(responses))
        monkeypatch.setattr(prompt, "select", lambda *a, **k: "revenue")

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
        def fake_ask(message, default=None):
            return default

        def fake_select(*args, default=None, **kwargs):
            return default

        monkeypatch.setattr(prompt, "ask", fake_ask)
        monkeypatch.setattr(prompt, "select", fake_select)

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
        monkeypatch.setattr(prompt, "ask", lambda *a, **k: "1001")

        assert prompt.prompt_account_identifier() == "1001"


@pytest.mark.unit
class TestConfirmAccountDeletion:
    def test_returns_true_when_confirmed(self, monkeypatch):
        monkeypatch.setattr(prompt, "confirm", lambda *a, **k: True)

        assert prompt.confirm_account_deletion("Cash") is True

    def test_returns_false_when_declined(self, monkeypatch):
        monkeypatch.setattr(prompt, "confirm", lambda *a, **k: False)

        assert prompt.confirm_account_deletion("Cash") is False

    def test_passes_expected_configuration_to_confirm(self, monkeypatch):
        captured = {}

        def fake_confirm(message, **kwargs):
            captured["message"] = message
            captured["kwargs"] = kwargs
            return False

        monkeypatch.setattr(prompt, "confirm", fake_confirm)

        prompt.confirm_account_deletion("Cash")

        assert captured["message"] == 'Delete account "Cash"?'
        assert captured["kwargs"]["default"] is False
        assert captured["kwargs"]["style"] == "error"
