import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_login_success(client: AsyncClient, test_admin_user):
    """Happy path: valid credentials return tokens."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "testadmin@test.com", "password": "TestAdmin@123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, test_admin_user):
    """Wrong password returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "testadmin@test.com", "password": "WrongPassword"},
    )
    assert response.status_code == 401


async def test_login_unknown_email(client: AsyncClient):
    """Unknown email returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.com", "password": "SomePassword@123"},
    )
    assert response.status_code == 401


async def test_get_me_authenticated(client: AsyncClient, admin_headers: dict):
    """GET /me returns current user data."""
    response = await client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testadmin@test.com"
    assert data["role"] == "system_admin"


async def test_get_me_unauthenticated(client: AsyncClient):
    """GET /me without token returns 401 or 403."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


async def test_refresh_token(client: AsyncClient, test_admin_user):
    """Refresh token returns new access token."""
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "testadmin@test.com", "password": "TestAdmin@123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_change_password(client: AsyncClient, admin_headers: dict):
    """Change password with correct current password succeeds."""
    response = await client.post(
        "/api/v1/auth/me/change-password",
        json={"current_password": "TestAdmin@123", "new_password": "NewAdmin@123"},
        headers=admin_headers,
    )
    assert response.status_code == 200

    # Restore password for other tests
    # (Get new token with new password)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "testadmin@test.com", "password": "NewAdmin@123"},
    )
    new_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    restore_response = await client.post(
        "/api/v1/auth/me/change-password",
        json={"current_password": "NewAdmin@123", "new_password": "TestAdmin@123"},
        headers=new_headers,
    )
    assert restore_response.status_code == 200


async def test_health_check(client: AsyncClient):
    """Health endpoint returns ok."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
