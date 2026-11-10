# SIIMS — School ICT Infrastructure Monitoring System

A centralised, locally-hosted monitoring and ICT asset management platform for a
school's ~40 Windows computers (scales to ~200). Monitor hardware health, network
status, software inventory, and software licences from one web dashboard — with
automatic fault detection, incident management, and reporting.

## Features

- **Central dashboard** — live computer status, CPU/RAM/disk charts, alerts, incidents.
- **Hardware monitoring** — CPU, RAM, disk, uptime, temperature (where exposed),
  SMART, battery (laptops), with configurable thresholds and deduplicated alerts.
- **Network monitoring** — heartbeat, latency, packet loss, gateway/DNS/server
  reachability, offline detection.
- **Software inventory** — automatic discovery via Windows Registry (not Win32_Product).
- **Licence management** — track seats, expiry dates, and assignments with reminders
  at 30/14/7 days and on expiry.
- **Incident management** — auto-created from critical alerts + manual reporting,
  assignment, resolution, and full history.
- **Preventive maintenance** — scheduling, recurring plans, completion records.
- **Notifications** — in-dashboard + optional email (SMTP).
- **Reporting** — PDF, Excel, and CSV for nine report types.
- **RBAC** — System Administrator, ICT Technician, School Management roles enforced
  on the backend.
- **Audit logs** — every significant action recorded.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy (async), Pydantic v2, Alembic |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts, TanStack Query |
| Database | PostgreSQL 16 |
| Agent | Python, psutil, Windows Registry, pywin32 (service), PyInstaller |
| Reports | ReportLab (PDF), openpyxl (Excel), csv |
| Auth | JWT (python-jose), bcrypt |
| Deployment | Docker Compose, nginx |

## Quick Start (Docker Compose)

```bash
# 1. Configure environment
cd deployment
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD, SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD

# 2. Build and run the whole stack
docker-compose up --build -d

# 3. Seed the admin account + sample data (first run only)
docker-compose exec backend python /database/seed_data.py

# 4. Open the dashboard
#    http://localhost   (log in with ADMIN_EMAIL / ADMIN_PASSWORD)
```

That starts PostgreSQL, the FastAPI backend, the built React frontend, and an nginx
reverse proxy. See the **Installation Guide** for manual (non-Docker) setup.

## Project Structure

```
SIIMS/
├── backend/            FastAPI app (models, schemas, APIs, services, workers)
│   ├── app/
│   ├── migrations/      Alembic migrations
│   └── tests/
├── frontend/           React + TypeScript SPA
│   └── src/            components, pages, services, hooks, types
├── monitoring-agent/   Windows monitoring agent (service + tests)
│   └── tests/
├── database/           schema.sql + seed_data.py
├── deployment/         docker-compose.yml, nginx config, .env.example
├── documentation/      architecture, database, install, agent, admin, user, troubleshooting
├── .env.example
└── README.md
```

## Documentation

| Document | Audience |
|----------|----------|
| [Installation Guide](documentation/installation-guide.md) | Anyone deploying SIIMS |
| [Architecture](documentation/architecture.md) | Developers / architects |
| [Database Design](documentation/database-design.md) | Developers / DBAs |
| [Administrator Guide](documentation/administrator-guide.md) | System Administrators |
| [Monitoring Agent Guide](documentation/monitoring-agent-guide.md) | Technicians deploying agents |
| [User Guide](documentation/user-guide.md) | ICT Technicians, School Management |
| [Troubleshooting](documentation/troubleshooting.md) | All users |

## Monitoring Workflow

1. Admin registers a computer in the dashboard and generates an agent API key.
2. The Windows agent (installed as a service) authenticates with that key and sends
   heartbeats every 60 seconds.
3. The backend stores metrics and evaluates them against thresholds.
4. Threshold breaches raise deduplicated alerts; critical ones auto-create incidents.
5. The offline-detection job marks computers offline when heartbeats stop.
6. The dashboard reflects live status; admins get notifications (and optional email).
7. Reports are generated on demand in PDF/Excel/CSV.

## Security & Privacy

- JWT auth + bcrypt hashing; RBAC enforced on every protected endpoint.
- Agents authenticate with a unique, hashed per-computer API key (shown once).
- Rate limiting on login; CORS restricted to the configured frontend origin.
- Sensitive values (licence keys, SMTP passwords) are stored as references / encrypted
  and never returned in full by the API.
- **SIIMS monitors computer health and authorised ICT asset information only.**
  It does not monitor personal activities, capture keystrokes, record screens, or
  collect personal files.

## Development

```bash
# Backend (development)
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python ../database/seed_data.py
uvicorn app.main:app --reload   # http://localhost:8000/docs

# Frontend (development, separate terminal)
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxies /api to :8000)

# Agent tests
cd monitoring-agent
pip install -r requirements.txt
pytest -v
```

## Licence

MIT. See the project header in each file. No paid third-party services or cloud
dependencies are required.
