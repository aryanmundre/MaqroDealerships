import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from maqro_backend.main import app
from maqro_backend.api.deps import get_current_user_id


client = TestClient(app)


@pytest.mark.asyncio
async def test_create_lead_unit():
    def get_fake_user_id():
        return "fake-user-id-for-testing"

    # Tell the app to use our fake function instead of the real one
    app.dependency_overrides[get_current_user_id] = get_fake_user_id

    lead_data = {
        "name": "Unit Test Lead",
        "email": "unit@test.com",
        "phone": "123-456-7890",
        "car": "Test Model S",
        "source": "Unit Test",
        "message": "This is a unit test."
    }

    with patch('maqro_backend.api.routes.leads.create_lead_with_initial_message', new_callable=AsyncMock) as mock_create_in_db:
        mock_create_in_db.return_value = {"lead_id": "mock-lead-uuid-123"}

        # 2. Act: Call the API. We don't need to send the header anymore.
        response = client.post(
            "/api/leads",
            json=lead_data
        )

        # 3. Assert: Check the results
        assert response.status_code == 200
        assert response.json() == {"lead_id": "mock-lead-uuid-123"}
        mock_create_in_db.assert_called_once()

    # Clean up the override after the test is done
    app.dependency_overrides = {} 