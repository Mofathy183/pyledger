"""Unit tests for the journal router: full Mapper -> Handler -> Presenter
chain, driven over real HTTP via `api_client` + `fake_container`.

Does NOT re-verify JournalService business rules (modules/journal/tests/),
mapper/presenter field-mapping in isolation (test_mapper.py,
test_presenter.py), or handler call-shape (test_handler.py). This tier
proves the wiring holds end-to-end and that errors surface as the
correct HTTP status/envelope via the registered exception handlers.
"""

import pytest

from pyledger.shared.errors import ErrorCode
from tests.factories import (
    make_create_account_request,
    make_create_journal_entry_request,
)


async def _seed_accounts(api_client):
    await api_client.post(
        "/accounts", json=make_create_account_request(code="1001", name="Cash")
    )
    await api_client.post(
        "/accounts",
        json=make_create_account_request(
            code="4001", name="Sales Revenue", category="REVENUE"
        ),
    )


@pytest.mark.unit
class TestCreateJournalEntryRoute:
    async def test_returns_201(self, api_client):
        await _seed_accounts(api_client)

        response = await api_client.post(
            "/journal-entries", json=make_create_journal_entry_request()
        )

        assert response.status_code == 201

    async def test_returns_created_entry_in_envelope(self, api_client):
        await _seed_accounts(api_client)

        response = await api_client.post(
            "/journal-entries", json=make_create_journal_entry_request()
        )

        body = response.json()
        assert body["success"] is True
        assert body["entry"]["journal_number"] == 1
        assert body["entry"]["is_balanced"] is True

    async def test_returns_404_when_account_unknown(self, api_client):
        response = await api_client.post(
            "/journal-entries", json=make_create_journal_entry_request()
        )

        assert response.status_code == 404
        assert response.json()["error_code"] == ErrorCode.UNKNOWN_ACCOUNT.value

    async def test_returns_422_when_entry_is_unbalanced(self, api_client):
        await _seed_accounts(api_client)

        response = await api_client.post(
            "/journal-entries",
            json=make_create_journal_entry_request(
                lines=[
                    {"account": "Cash", "debit_amount": "100", "credit_amount": "0"},
                    {
                        "account": "Sales Revenue",
                        "debit_amount": "0",
                        "credit_amount": "50",
                    },
                ]
            ),
        )

        assert response.status_code == 422
        assert response.json()["error_code"] == ErrorCode.VALIDATION_ERROR.value

    async def test_returns_422_on_missing_required_field(self, api_client):
        response = await api_client.post("/journal-entries", json={"lines": []})

        assert response.status_code == 422


@pytest.mark.unit
class TestListJournalEntriesRoute:
    async def test_returns_200(self, api_client):
        response = await api_client.get("/journal-entries")

        assert response.status_code == 200

    async def test_returns_empty_list_when_no_entries(self, api_client):
        response = await api_client.get("/journal-entries")

        assert response.json()["entries"] == []

    async def test_returns_created_entries(self, api_client):
        await _seed_accounts(api_client)
        await api_client.post(
            "/journal-entries", json=make_create_journal_entry_request()
        )
        await api_client.post(
            "/journal-entries", json=make_create_journal_entry_request()
        )

        response = await api_client.get("/journal-entries")

        numbers = [e["journal_number"] for e in response.json()["entries"]]
        assert numbers == [1, 2]


@pytest.mark.unit
class TestGetJournalEntryRoute:
    async def test_returns_200_for_existing_entry(self, api_client):
        await _seed_accounts(api_client)
        await api_client.post(
            "/journal-entries", json=make_create_journal_entry_request()
        )

        response = await api_client.get("/journal-entries/1")

        assert response.status_code == 200
        assert response.json()["entry"]["journal_number"] == 1

    async def test_returns_404_for_unknown_journal_number(self, api_client):
        response = await api_client.get("/journal-entries/999")

        assert response.status_code == 404
        assert response.json()["error_code"] == ErrorCode.UNKNOWN_JOURNAL_ENTRY.value
