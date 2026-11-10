import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_list_computers_authenticated(client: AsyncClient, admin_headers: dict):
    """List computers returns paginated result."""
    response = await client.get("/api/v1/computers/", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data


async def test_list_computers_unauthenticated(client: AsyncClient):
    """List computers without auth returns 401/403."""
    response = await client.get("/api/v1/computers/")
    assert response.status_code in (401, 403)


async def test_create_computer_as_admin(client: AsyncClient, admin_headers: dict):
    """Admin can create a computer."""
    response = await client.post(
        "/api/v1/computers/",
        json={
            "hostname": "PC-TEST-001",
            "ip_address": "192.168.1.100",
            "operating_system": "Windows 11",
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["hostname"] == "PC-TEST-001"
    assert data["status"] == "unknown"
    return data["id"]


async def test_create_computer_as_technician_forbidden(client: AsyncClient, tech_headers: dict):
    """Technician cannot create a computer (admin only)."""
    response = await client.post(
        "/api/v1/computers/",
        json={"hostname": "PC-TECH-TEST"},
        headers=tech_headers,
    )
    assert response.status_code == 403


async def test_get_computer_not_found(client: AsyncClient, admin_headers: dict):
    """Get non-existent computer returns 404."""
    response = await client.get("/api/v1/computers/999999", headers=admin_headers)
    assert response.status_code == 404


async def test_create_duplicate_hostname(client: AsyncClient, admin_headers: dict):
    """Creating a computer with duplicate hostname returns 400."""
    # First create
    await client.post(
        "/api/v1/computers/",
        json={"hostname": "PC-DUPE-TEST"},
        headers=admin_headers,
    )
    # Duplicate
    response = await client.post(
        "/api/v1/computers/",
        json={"hostname": "PC-DUPE-TEST"},
        headers=admin_headers,
    )
    assert response.status_code == 400


async def test_update_computer_as_admin(client: AsyncClient, admin_headers: dict):
    """Admin can update a computer."""
    # Create first
    create_resp = await client.post(
        "/api/v1/computers/",
        json={"hostname": "PC-UPDATE-TEST"},
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    computer_id = create_resp.json()["id"]

    # Update
    update_resp = await client.put(
        f"/api/v1/computers/{computer_id}",
        json={"department": "ICT Department"},
        headers=admin_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["department"] == "ICT Department"
