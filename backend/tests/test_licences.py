import pytest
from httpx import AsyncClient
from datetime import date, timedelta


pytestmark = pytest.mark.asyncio


async def test_list_licences(client: AsyncClient, admin_headers: dict):
    """List licences returns a list."""
    response = await client.get("/api/v1/licences/", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_create_licence_as_admin(client: AsyncClient, admin_headers: dict):
    """Admin can create a licence."""
    expiry = (date.today() + timedelta(days=60)).isoformat()
    response = await client.post(
        "/api/v1/licences/",
        json={
            "software_name": "Microsoft Office 2024",
            "vendor": "Microsoft",
            "seats": 25,
            "expiry_date": expiry,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["software_name"] == "Microsoft Office 2024"
    assert data["seats"] == 25
    return data["id"]


async def test_create_licence_as_technician_forbidden(client: AsyncClient, tech_headers: dict):
    """Technician cannot create licences."""
    response = await client.post(
        "/api/v1/licences/",
        json={"software_name": "Some Software"},
        headers=tech_headers,
    )
    assert response.status_code == 403


async def test_get_licence_not_found(client: AsyncClient, admin_headers: dict):
    """Get non-existent licence returns 404."""
    response = await client.get("/api/v1/licences/999999", headers=admin_headers)
    assert response.status_code == 404


async def test_get_expiring_licences(client: AsyncClient, admin_headers: dict):
    """Expiring licences endpoint returns a list."""
    response = await client.get("/api/v1/licences/expiring", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_update_licence(client: AsyncClient, admin_headers: dict):
    """Admin can update a licence."""
    # Create first
    create_resp = await client.post(
        "/api/v1/licences/",
        json={"software_name": "Adobe Acrobat", "seats": 5},
        headers=admin_headers,
    )
    licence_id = create_resp.json()["id"]

    # Update
    update_resp = await client.put(
        f"/api/v1/licences/{licence_id}",
        json={"vendor": "Adobe Inc."},
        headers=admin_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["vendor"] == "Adobe Inc."


async def test_delete_licence(client: AsyncClient, admin_headers: dict):
    """Admin can deactivate a licence."""
    create_resp = await client.post(
        "/api/v1/licences/",
        json={"software_name": "ToDelete Software"},
        headers=admin_headers,
    )
    licence_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/licences/{licence_id}", headers=admin_headers)
    assert del_resp.status_code == 200


async def test_licences_unauthenticated(client: AsyncClient):
    """Licences endpoints require auth."""
    response = await client.get("/api/v1/licences/")
    assert response.status_code in (401, 403)
