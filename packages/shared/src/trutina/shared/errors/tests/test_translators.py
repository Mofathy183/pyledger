import pytest
from pydantic import BaseModel, Field, ValidationError
from pydantic_core import PydanticCustomError
from trutina.shared.errors import ErrorCode
from trutina.shared.errors.errors import FieldViolation
from trutina.shared.errors.translators import (
    get_field_violations,
    pydantic_error,
)


@pytest.mark.unit
class TestPydanticError:
    def test_returns_custom_error_with_matching_type(self):
        error = pydantic_error(ErrorCode.INVALID_ACCOUNT_NAME)

        assert isinstance(error, PydanticCustomError)
        assert error.type == ErrorCode.INVALID_ACCOUNT_NAME


@pytest.mark.unit
class TestGetFieldViolations:
    def test_preserves_supported_pydantic_error_codes(self):
        class Model(BaseModel):
            name: str

        with pytest.raises(ValidationError) as exc_info:
            Model(name=123)  # ty:ignore[invalid-argument-type]

        violations = get_field_violations(exc_info.value)

        assert len(violations) == 1
        assert violations[0].code == ErrorCode.STRING_TYPE

    def test_maps_string_too_short_to_matching_error_code(self):
        class Model(BaseModel):
            name: str = Field(min_length=2)

        with pytest.raises(ValidationError) as exc_info:
            Model(name="")

        violations = get_field_violations(exc_info.value)

        assert len(violations) == 1

        violation = violations[0]

        assert violation.code == ErrorCode.STRING_TOO_SHORT
        assert violation.field == "name"
        assert violation.value == ""

    def test_downgrades_domain_error_codes_to_unknown_error(self):
        class Model(BaseModel):
            value: str

            @classmethod
            def validate_value(cls, value: str) -> str:
                raise pydantic_error(ErrorCode.INVALID_ACCOUNT_NAME)

        class DomainModel(BaseModel):
            value: str

            @classmethod
            def __get_pydantic_core_schema__(cls, source, handler):
                return handler(source)

        class AccountNameModel(BaseModel):
            value: str

            @staticmethod
            def _raise_error(value: str) -> str:
                raise pydantic_error(ErrorCode.INVALID_ACCOUNT_NAME)

        from pydantic import field_validator

        class InvalidAccountNameModel(BaseModel):
            value: str

            @field_validator("value")
            @classmethod
            def validate_value(cls, value: str) -> str:
                raise pydantic_error(ErrorCode.INVALID_ACCOUNT_NAME)

        with pytest.raises(ValidationError) as exc_info:
            InvalidAccountNameModel(value="bad")

        violations = get_field_violations(exc_info.value)

        assert len(violations) == 1
        assert violations[0].code == ErrorCode.UNKNOWN_ERROR
        assert violations[0].field == "value"
        assert violations[0].value == ErrorCode.INVALID_ACCOUNT_NAME

    def test_preserves_raw_domain_code_in_value_when_downgraded(self):

        from pydantic import field_validator

        class InvalidAccountNameModel(BaseModel):
            value: str

            @field_validator("value")
            @classmethod
            def validate_value(cls, value: str) -> str:
                raise pydantic_error(ErrorCode.INVALID_ACCOUNT_NAME)

        with pytest.raises(ValidationError) as exc_info:
            InvalidAccountNameModel(value="bad")

        violations = get_field_violations(exc_info.value)

        violation = violations[0]

        assert violation.code == ErrorCode.UNKNOWN_ERROR
        assert violation.value == ErrorCode.INVALID_ACCOUNT_NAME

    def test_joins_nested_field_locations(self):

        class Child(BaseModel):
            name: str

        class Parent(BaseModel):
            children: list[Child]

        with pytest.raises(ValidationError) as exc_info:
            Parent(children=[{"name": 123}])

        violations = get_field_violations(exc_info.value)

        assert len(violations) == 1
        assert violations[0].field == "children.0.name"

    def test_returns_multiple_violations_in_order(self):
        class Model(BaseModel):
            first: str
            second: str

        with pytest.raises(ValidationError) as exc_info:
            Model(first=123, second=456)  # ty:ignore[invalid-argument-type]

        violations = get_field_violations(exc_info.value)

        assert len(violations) == 2

        assert isinstance(violations[0], FieldViolation)
        assert isinstance(violations[1], FieldViolation)

        assert violations[0].field == "first"
        assert violations[1].field == "second"
