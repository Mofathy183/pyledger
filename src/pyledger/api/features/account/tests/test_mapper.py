"""Unit tests for the account feature's Request Schema -> Input DTO mapping.

Pure construction only -- no service calls, no domain validation (that
fires later, inside the Handler's call into AccountService).
"""

import pytest

from pyledger.api.features.account.mapper import (
    to_create_account_input,
    to_update_account_input,
)
from pyledger.api.features.account.schemas import (
    CreateAccountRequest,
    UpdateAccountRequest,
)
from pyledger.modules.account.dtos import CreateAccountInput, UpdateAccountInput
from pyledger.modules.account.schemas.account import AccountCategory


@pytest.mark.unit
class TestToCreateAccountInput:
    def test_maps_code(self):
        request = CreateAccountRequest(
            code="1001", name="Cash", category=AccountCategory.ASSET
        )

        dto = to_create_account_input(request)

        assert dto.code == "1001"

    def test_maps_name(self):
        request = CreateAccountRequest(
            code="1001", name="Cash", category=AccountCategory.ASSET
        )

        dto = to_create_account_input(request)

        assert dto.name == "Cash"

    def test_maps_category(self):
        request = CreateAccountRequest(
            code="4001", name="Sales Revenue", category=AccountCategory.REVENUE
        )

        dto = to_create_account_input(request)

        assert dto.category is AccountCategory.REVENUE

    def test_returns_create_account_input_instance(self):
        request = CreateAccountRequest(
            code="1001", name="Cash", category=AccountCategory.ASSET
        )

        dto = to_create_account_input(request)

        assert isinstance(dto, CreateAccountInput)


@pytest.mark.unit
class TestToUpdateAccountInput:
    def test_maps_code_from_path_argument(self):
        request = UpdateAccountRequest(name="Main Cash")

        dto = to_update_account_input("1001", request)

        assert dto.code == "1001"

    def test_maps_name_when_provided(self):
        request = UpdateAccountRequest(name="Main Cash")

        dto = to_update_account_input("1001", request)

        assert dto.name == "Main Cash"

    def test_maps_none_name_when_omitted(self):
        request = UpdateAccountRequest()

        dto = to_update_account_input("1001", request)

        assert dto.name is None

    def test_maps_category_when_provided(self):
        request = UpdateAccountRequest(category=AccountCategory.EXPENSE)

        dto = to_update_account_input("1001", request)

        assert dto.category is AccountCategory.EXPENSE

    def test_maps_none_category_when_omitted(self):
        request = UpdateAccountRequest()

        dto = to_update_account_input("1001", request)

        assert dto.category is None

    def test_returns_update_account_input_instance(self):
        request = UpdateAccountRequest()

        dto = to_update_account_input("1001", request)

        assert isinstance(dto, UpdateAccountInput)
