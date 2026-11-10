import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.users import User, UserRole


# Use SQLite in-memory for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Create all tables in the test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean database session per test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Async test client for the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def test_admin_user(db_session: AsyncSession) -> User:
    """Get or create a system_admin test user."""
    from sqlalchemy import select as sa_select
    result = await db_session.execute(
        sa_select(User).where(User.email == "testadmin@test.com")
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    user = User(
        email="testadmin@test.com",
        full_name="Test Admin",
        hashed_password=hash_password("TestAdmin@123"),
        role=UserRole.system_admin,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_technician_user(db_session: AsyncSession) -> User:
    """Get or create an ict_technician test user."""
    from sqlalchemy import select as sa_select
    result = await db_session.execute(
        sa_select(User).where(User.email == "testtech@test.com")
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    user = User(
        email="testtech@test.com",
        full_name="Test Technician",
        hashed_password=hash_password("TestTech@123"),
        role=UserRole.ict_technician,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _get_auth_headers(client: AsyncClient, email: str, password: str) -> dict:
    """Log in and return auth headers."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient, test_admin_user: User) -> dict:
    """Auth headers for the test admin user."""
    return await _get_auth_headers(client, "testadmin@test.com", "TestAdmin@123")


@pytest_asyncio.fixture
async def tech_headers(client: AsyncClient, test_technician_user: User) -> dict:
    """Auth headers for the test technician user."""
    return await _get_auth_headers(client, "testtech@test.com", "TestTech@123")
