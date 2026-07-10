import pytest

from pyledger.api.shared.errors.schemas import (
    ErrorResponse,
    FieldErrorDetail,
    ValidationErrorResponse,
)


@pytest.mark.unit
class TestErrorResponse:
    def test_success_is_always_false(self):
        response = ErrorResponse(error_code="account.unknown", message="msg")

        assert response.success is False

    def test_hint_defaults_to_none(self):
        response = ErrorResponse(error_code="account.unknown", message="msg")

        assert response.hint is None

    def test_accepts_explicit_hint(self):
        response = ErrorResponse(
            error_code="account.unknown", message="msg", hint="try again"
        )

        assert response.hint == "try again"


@pytest.mark.unit
class TestValidationErrorResponse:
    def test_details_defaults_to_empty_list(self):
        response = ValidationErrorResponse(error_code="error.validation", message="msg")

        assert response.details == []

    def test_accepts_field_error_details(self):
        detail = FieldErrorDetail(
            field="name", code="account.invalid_name", message="msg"
        )

        response = ValidationErrorResponse(
            error_code="error.validation", message="msg", details=[detail]
        )

        assert response.details == [detail]

    def test_inherits_error_response_fields(self):
        response = ValidationErrorResponse(error_code="error.validation", message="msg")

        assert response.success is False


@pytest.mark.unit
class TestFieldErrorDetail:
    def test_creates_with_valid_values(self):
        detail = FieldErrorDetail(field="name", code="string_too_short", message="msg")

        assert detail.field == "name"
        assert detail.code == "string_too_short"
        assert detail.message == "msg"
