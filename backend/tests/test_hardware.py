import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_get_hardware_metrics(client: AsyncClient, admin_headers: dict):
    """Hardware metrics endpoint returns a list."""
    response = await client.get("/api/v1/hardware/metrics", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_get_hardware_alerts(client: AsyncClient, admin_headers: dict):
    """Hardware alerts endpoint returns a list."""
    response = await client.get("/api/v1/hardware/alerts", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_get_thresholds(client: AsyncClient, admin_headers: dict):
    """Get thresholds returns expected keys."""
    response = await client.get("/api/v1/hardware/thresholds", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "cpu_warning_percent" in data
    assert "ram_warning_percent" in data
    assert "disk_warning_percent" in data
    assert "disk_critical_percent" in data


async def test_get_thresholds_as_technician(client: AsyncClient, tech_headers: dict):
    """Technician can read thresholds."""
    response = await client.get("/api/v1/hardware/thresholds", headers=tech_headers)
    assert response.status_code == 200


async def test_update_thresholds_as_admin(client: AsyncClient, admin_headers: dict):
    """Admin can update thresholds."""
    response = await client.put(
        "/api/v1/hardware/thresholds",
        json={"cpu_warning_percent": 85.0},
        headers=admin_headers,
    )
    assert response.status_code == 200


async def test_update_thresholds_as_technician_forbidden(client: AsyncClient, tech_headers: dict):
    """Technician cannot update thresholds."""
    response = await client.put(
        "/api/v1/hardware/thresholds",
        json={"cpu_warning_percent": 85.0},
        headers=tech_headers,
    )
    assert response.status_code == 403


async def test_hardware_unauthenticated(client: AsyncClient):
    """Hardware endpoints require auth."""
    response = await client.get("/api/v1/hardware/metrics")
    assert response.status_code in (401, 403)
