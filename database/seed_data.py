#!/usr/bin/env python3
"""
# TEST DATA — do not use in production without changing passwords.

Seed script: Creates admin user, additional users, locations, and default system settings.
Run from the repo root: python database/seed_data.py
"""

import asyncio
import sys
import os

# Locate the backend package regardless of where this script runs:
#   - from the repo (database/seed_data.py → ../backend has app/)
#   - inside the Docker container (mounted at /database, backend at /app)
_here = os.path.dirname(os.path.abspath(__file__))
_candidates = [
    os.path.join(_here, "..", "backend"),  # repo layout
    _here,                                  # if placed inside backend/
    os.path.join(_here, ".."),              # if placed at backend/seed_data.py
    "/app",                                  # Docker container WORKDIR
]
for _c in _candidates:
    if os.path.isdir(os.path.join(_c, "app")):
        sys.path.insert(0, _c)
        break

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import engine, AsyncSessionLocal, Base
from app.core.security import hash_password
from app.core.config import settings
from app.models.users import User, UserRole
from app.models.locations import Location
from app.models.system_settings import SystemSetting


LOCATIONS = [
    {"name": "Main Computer Lab", "description": "Primary ICT laboratory with 20 computers", "building": "Block A", "floor": "Ground"},
    {"name": "Science Lab", "description": "Science department computer lab", "building": "Block B", "floor": "1st"},
    {"name": "Admin Office", "description": "Administration department computers", "building": "Main Block", "floor": "Ground"},
    {"name": "Library", "description": "Library research computers", "building": "Library Block", "floor": "Ground"},
    {"name": "Staff Room", "description": "Staff workstations", "building": "Main Block", "floor": "1st"},
]

USERS = [
    {
        "email": "technician1@school.edu",
        "full_name": "John Technician",
        "password": "Tech@123456",
        "role": UserRole.ict_technician,
        "phone": "+1234567891",
    },
    {
        "email": "technician2@school.edu",
        "full_name": "Jane Technician",
        "password": "Tech@123456",
        "role": UserRole.ict_technician,
        "phone": "+1234567892",
    },
    {
        "email": "management@school.edu",
        "full_name": "School Principal",
        "password": "Mgmt@123456",
        "role": UserRole.school_management,
        "phone": "+1234567893",
    },
]

SYSTEM_SETTINGS = [
    ("cpu_warning_percent", "90", "float", "thresholds"),
    ("ram_warning_percent", "90", "float", "thresholds"),
    ("disk_warning_percent", "90", "float", "thresholds"),
    ("disk_critical_percent", "95", "float", "thresholds"),
    ("offline_timeout_minutes", "10", "integer", "monitoring"),
    ("heartbeat_interval_seconds", "60", "integer", "monitoring"),
    ("software_scan_interval_hours", "24", "integer", "monitoring"),
    ("data_retention_days", "30", "integer", "monitoring"),
    ("smtp_host", "", "string", "smtp"),
    ("smtp_port", "587", "integer", "smtp"),
    ("smtp_user", "", "string", "smtp"),
    ("smtp_password_encrypted", "", "string", "smtp"),
    ("smtp_from", "", "string", "smtp"),
]


async def seed_database():
    """Run all seed operations."""
    print("=" * 60)
    print("SIIMS Database Seed Script")
    print("# TEST DATA — do not use in production")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        # --- Admin user ---
        admin_email = settings.ADMIN_EMAIL
        admin_password = settings.ADMIN_PASSWORD

        existing_admin = await db.execute(
            select(User).where(User.email == admin_email)
        )
        if existing_admin.scalar_one_or_none():
            print(f"Admin user already exists: {admin_email}")
        else:
            admin = User(
                email=admin_email,
                full_name="System Administrator",
                hashed_password=hash_password(admin_password),
                role=UserRole.system_admin,
                is_active=True,
                phone="+1234567890",
            )
            db.add(admin)
            print(f"Created admin: {admin_email}")

        # --- Additional users ---
        for user_data in USERS:
            existing = await db.execute(
                select(User).where(User.email == user_data["email"])
            )
            if existing.scalar_one_or_none():
                print(f"User already exists: {user_data['email']}")
                continue
            user = User(
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password=hash_password(user_data["password"]),
                role=user_data["role"],
                is_active=True,
                phone=user_data.get("phone"),
            )
            db.add(user)
            print(f"Created user: {user_data['email']} ({user_data['role']})")

        # --- Locations ---
        for loc_data in LOCATIONS:
            existing = await db.execute(
                select(Location).where(Location.name == loc_data["name"])
            )
            if existing.scalar_one_or_none():
                print(f"Location already exists: {loc_data['name']}")
                continue
            location = Location(**loc_data)
            db.add(location)
            print(f"Created location: {loc_data['name']}")

        # --- System settings ---
        for key, value, value_type, category in SYSTEM_SETTINGS:
            existing = await db.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            if existing.scalar_one_or_none():
                continue  # Don't override existing settings
            setting = SystemSetting(
                key=key,
                value=value,
                value_type=value_type,
                category=category,
            )
            db.add(setting)
        print("System settings initialized")

        await db.commit()

    print("=" * 60)
    print("Seed complete!")
    print(f"Admin login: {settings.ADMIN_EMAIL} / {settings.ADMIN_PASSWORD}")
    print("Change the admin password immediately after first login.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_database())
