import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from maqro_backend.main import app
from maqro_backend.api.deps import get_current_user_id, get_db_session
from datetime import datetime
import pytz

# A single TestClient instance is used for all tests in this file
client = TestClient(app)

# --- Test for POST /api/leads ---
@pytest.mark.asyncio
async def test_create_lead_unit():
    # Arrange: Override dependencies for this test
    app.dependency_overrides[get_current_user_id] = lambda: "fake-user-id"
    app.dependency_overrides[get_db_session] = lambda: None # Mock the db session

    lead_data = {
        "name": "Unit Test Lead",
        "email": "unit@test.com",
        "phone": "123-456-7890",
        "car_interest": "Test Model S",
        "source": "Unit Test",
        "message": "This is a unit test."
    }

    with patch('maqro_backend.api.routes.leads.create_lead_with_initial_message', new_callable=AsyncMock) as mock_create_in_db:
        mock_create_in_db.return_value = {"lead_id": "mock-lead-uuid-123"}

        # Act: Call the API
        response = client.post("/api/leads", json=lead_data)

        # Assert: Check the results
        assert response.status_code == 200
        assert response.json() == {"lead_id": "mock-lead-uuid-123"}
        mock_create_in_db.assert_called_once()

    # Cleanup the overrides after the test
    app.dependency_overrides = {}


# --- Tests for GET /api/leads ---
@pytest.mark.asyncio
async def test_get_all_leads_unit():
    """
    Tests getting a list of all leads for a user.
    """
    # Arrange: Override dependencies and prepare mock data
    app.dependency_overrides[get_current_user_id] = lambda: "test-user-1"
    app.dependency_overrides[get_db_session] = lambda: None # Mock the db session

    mock_lead_1 = MagicMock()
    mock_lead_1.id = "lead-uuid-1"
    mock_lead_1.name = "First Lead"
    mock_lead_1.email = "first@test.com"
    mock_lead_1.phone = "111"
    mock_lead_1.car_interest = "Car A"
    mock_lead_1.source = "Website"
    mock_lead_1.status = "New"
    mock_lead_1.last_contact_at = datetime.now(pytz.utc)
    mock_lead_1.message = "Message 1"
    mock_lead_1.user_id = "test-user-1"
    mock_lead_1.created_at = datetime.now(pytz.utc)

    with patch('maqro_backend.api.routes.leads.get_all_leads_ordered', new_callable=AsyncMock) as mock_get_from_db:
        mock_get_from_db.return_value = [mock_lead_1]

        # Act: Call the API
        response = client.get("/api/leads")

        # Assert: Check the response
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 1
        assert response_data[0]["name"] == "First Lead"
        assert response_data[0]["id"] == "lead-uuid-1"
        mock_get_from_db.assert_called_once_with(session=None, user_id="test-user-1")

    # Cleanup
    app.dependency_overrides = {}


# --- Tests for GET /api/leads/{lead_id} ---
@pytest.mark.asyncio
async def test_get_lead_by_id_success():
    """
    Tests successfully getting a single lead by its ID.
    """
    # Arrange
    current_user = "test-user-1"
    app.dependency_overrides[get_current_user_id] = lambda: current_user
    app.dependency_overrides[get_db_session] = lambda: None # Mock the db session

    mock_lead = MagicMock()
    mock_lead.user_id = str(current_user)
    mock_lead.id = "lead-uuid-1"
    mock_lead.name = "My Lead"
    mock_lead.email="my@lead.com"; mock_lead.phone="222"; mock_lead.car_interest="Car B"; 
    mock_lead.source="Test"; mock_lead.status="Active"; mock_lead.last_contact_at=datetime.now(pytz.utc); mock_lead.message="Hi"; mock_lead.created_at=datetime.now(pytz.utc)

    with patch('maqro_backend.api.routes.leads.get_lead_by_id', new_callable=AsyncMock) as mock_get_from_db:
        mock_get_from_db.return_value = mock_lead

        # Act
        response = client.get("/api/leads/lead-uuid-1")

        # Assert
        assert response.status_code == 200
        assert response.json()["name"] == "My Lead"
        mock_get_from_db.assert_called_once()
        
    # Cleanup
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_get_lead_by_id_not_found():
    """
    Tests the 404 Not Found error if the lead ID doesn't exist.
    """
    # Arrange
    app.dependency_overrides[get_current_user_id] = lambda: "any-user"
    app.dependency_overrides[get_db_session] = lambda: None # Mock the db session
    
    with patch('maqro_backend.api.routes.leads.get_lead_by_id', new_callable=AsyncMock) as mock_get_from_db:
        mock_get_from_db.return_value = None

        # Act
        response = client.get("/api/leads/non-existent-uuid")

        # Assert
        assert response.status_code == 404
        assert response.json() == {"detail": "Lead not found"}

    # Cleanup
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_lead_by_id_access_denied():
    """
    Tests the 403 Access Denied error if the lead belongs to another user.
    """
    # Arrange
    app.dependency_overrides[get_current_user_id] = lambda: "current-user-id"
    app.dependency_overrides[get_db_session] = lambda: None # Mock the db session

    mock_lead = MagicMock()
    mock_lead.user_id = "a-different-user-id"

    with patch('maqro_backend.api.routes.leads.get_lead_by_id', new_callable=AsyncMock) as mock_get_from_db:
        mock_get_from_db.return_value = mock_lead

        # Act
        response = client.get("/api/leads/some-other-persons-lead-uuid")

        # Assert
        assert response.status_code == 403
        assert response.json() == {"detail": "Access denied"}

    # Cleanup
    app.dependency_overrides = {}
