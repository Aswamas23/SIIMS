import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_list_incidents(client: AsyncClient, admin_headers: dict):
    """List incidents returns a list."""
    response = await client.get("/api/v1/incidents/", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_create_incident(client: AsyncClient, admin_headers: dict):
    """Create an incident with valid data."""
    response = await client.post(
        "/api/v1/incidents/",
        json={
            "title": "Test Incident",
            "description": "This is a test incident",
            "category": "other",
            "severity": "medium",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Incident"
    assert "incident_number" in data
    assert data["incident_number"].startswith("INC-")
    assert data["status"] == "open"
    return data["id"]


async def test_get_incident_not_found(client: AsyncClient, admin_headers: dict):
    """Get non-existent incident returns 404."""
    response = await client.get("/api/v1/incidents/999999", headers=admin_headers)
    assert response.status_code == 404


async def test_resolve_incident(client: AsyncClient, admin_headers: dict):
    """Resolve an incident."""
    # Create
    create_resp = await client.post(
        "/api/v1/incidents/",
        json={"title": "Incident to resolve", "severity": "low", "category": "other"},
        headers=admin_headers,
    )
    incident_id = create_resp.json()["id"]

    # Resolve
    resolve_resp = await client.post(
        f"/api/v1/incidents/{incident_id}/resolve",
        json={"resolution_notes": "Issue fixed"},
        headers=admin_headers,
    )
    assert resolve_resp.status_code == 200

    # Verify status
    get_resp = await client.get(f"/api/v1/incidents/{incident_id}", headers=admin_headers)
    assert get_resp.json()["status"] == "resolved"


async def test_add_incident_update(client: AsyncClient, admin_headers: dict):
    """Add a comment to an incident."""
    # Create
    create_resp = await client.post(
        "/api/v1/incidents/",
        json={"title": "Incident with update", "severity": "low", "category": "other"},
        headers=admin_headers,
    )
    incident_id = create_resp.json()["id"]

    # Add update
    update_resp = await client.post(
        f"/api/v1/incidents/{incident_id}/update",
        json={"message": "Investigating the issue", "update_type": "comment"},
        headers=admin_headers,
    )
    assert update_resp.status_code == 200


async def test_incidents_unauthenticated(client: AsyncClient):
    """Incidents endpoints require auth."""
    response = await client.get("/api/v1/incidents/")
    assert response.status_code in (401, 403)
