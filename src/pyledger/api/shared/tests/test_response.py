from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from pyledger.api.shared.response import BaseResponse, SuccessResponse


@pytest.mark.unit
class TestBaseResponse:
    def test_requires_success_field(self):
        with pytest.raises(ValidationError):
            BaseResponse()  # ty:ignore[missing-argument]

    def test_timestamp_defaults_to_now(self):
        before = datetime.now(UTC)

        response = BaseResponse(success=True)

        after = datetime.now(UTC)
        assert before <= response.timestamp <= after


@pytest.mark.unit
class TestSuccessResponse:
    def test_success_defaults_to_true(self):
        response = SuccessResponse()

        assert response.success is True
