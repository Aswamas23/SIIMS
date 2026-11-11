# SIIMS — Installation Guide

## Prerequisites

| Component | Minimum Version |
|-----------|-----------------|
| Python    | 3.11+           |
| Node.js   | 20+             |
| PostgreSQL | 16+            |
| Docker    | 24+ (optional)  |
| nginx     | 1.25+ (manual)  |

---

## Option A — Docker Compose (Recommended)

The fastest way to get the full stack running.

### Step 1 — Clone or copy the SIIMS folder onto the server.

### Step 2 — Copy the environment template.
```bash
cd deployment
cp .env.example .env
```

### Step 3 — Edit `.env` with real values.
Minimum required:
- `POSTGRES_PASSWORD` — set a strong random password.
- `SECRET_KEY` — generate with:
  `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- `ADMIN_EMAIL` — email for the first administrator account.
- `ADMIN_PASSWORD` — a strong initial password (change after first login).

### Step 4 — Build and start all containers.
```bash
docker-compose up --build -d
```

### Step 5 — Seed the database (first run only).
```bash
    docker-compose exec backend python -c "
    import asyncio, os
    from app.core.database import async_sessionmaker, engine
    from app.models import *
    from app.core.security import hash_password
    from app.models.users import User, UserRole

async def seed():
    from app.core.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Alembic runs automatically on backend startup.
    print('Database ready.')

asyncio.run(seed())
"
```
Or use the seed script:
```bash
docker-compose exec backend python /database/seed_data.py
```

### Step 6 — Verify.
- Dashboard: http://localhost
- API health: http://localhost/api/v1/health
- API docs: http://localhost:8000/docs (direct to backend port)

Log in with the ADMIN_EMAIL and ADMIN_PASSWORD you configured.

---

## Option B — Manual Installation (Windows Server / Linux)

### 1. PostgreSQL Setup

**Linux (Ubuntu/Debian):**
```bash
sudo apt install postgresql-16
sudo -u postgres createuser --pwprompt siims
sudo -u postgres createdb -O siims siims
```

**Windows Server:**
Download and install PostgreSQL 16 from postgresql.org.
Create user `siims` and database `siims` via pgAdmin or psql.

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Linux
.venv\Scripts\activate      # Windows

pip install -r requirements.txt

cp ../.env.example .env     # Then edit .env with real values

# Run database migrations
alembic upgrade head

# Seed first admin account
python ../database/seed_data.py

# Start the API server (development)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Production (systemd, Linux):**
Create `/etc/systemd/system/siims-backend.service`:
```ini
[Unit]
Description=SIIMS FastAPI Backend
After=network.target postgresql.service

[Service]
Type=exec
User=siims
WorkingDirectory=/opt/siims/backend
EnvironmentFile=/opt/siims/backend/.env
ExecStart=/opt/siims/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable siims-backend
sudo systemctl start siims-backend
```

### 3. Frontend Build
```bash
cd frontend
cp .env.example .env     # Set VITE_API_BASE_URL=http://<server-ip>
npm install
npm run build
# This produces frontend/dist/
```

### 4. nginx Configuration (manual)
```bash
sudo apt install nginx
```
Copy `deployment/nginx/nginx.conf` to `/etc/nginx/nginx.conf` and
update the upstream hostnames to `127.0.0.1:8000` for the backend.
Point the frontend location to `frontend/dist/`.

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 5. HTTPS Setup
Obtain a certificate (Let's Encrypt recommended for internet-accessible deployments;
use a self-signed certificate for LAN-only deployments):
```bash
sudo certbot --nginx -d siims.school.edu
```
Then uncomment the HTTPS block in nginx.conf.

---

## First Login

1. Open http://\<server-ip\> in a browser.
2. Log in with the ADMIN_EMAIL and ADMIN_PASSWORD from `.env`.
3. Go to **Settings → General** and update the school name.
4. Go to **Users** and create accounts for technicians and management.
5. Go to **Computers** and register your first computer.
6. Follow the **Monitoring Agent Guide** to deploy an agent to that computer.

---

## Backup & Restoration

**Backup:**
```bash
# Docker
docker-compose exec postgres pg_dump -U siims siims > backup_$(date +%Y%m%d).sql

# Manual
pg_dump -U siims -h localhost siims > backup.sql
```

**Restore:**
```bash
# Docker (restore into a running container)
docker-compose exec -T postgres psql -U siims siims < backup.sql

# Manual
psql -U siims -h localhost siims < backup.sql
```

**Automated backups:** configure a cron job or Windows Task Scheduler to run the
`pg_dump` command daily and retain the last N files.

---

## Upgrading SIIMS

1. Pull/copy the new SIIMS folder.
2. Run `alembic upgrade head` (backend migrations).
3. Rebuild containers or restart services.
4. Clear browser cache if the frontend changed.
