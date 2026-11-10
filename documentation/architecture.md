# SIIMS — System Architecture

## Overview

SIIMS (School ICT Infrastructure Monitoring System) is a centralised client-server
application that monitors a fleet of Windows computers across a school's laboratories,
offices, and departments from a single web dashboard.

```
                       +-----------------------+
                       |   School ICT Admin     |
                       |   (web browser)        |
                       +-----------+-----------+
                                   |
                                   v
                         +-------------------+
                         |   nginx (rev.proxy)|
                         |   :80 / :443        |
                         +---+----------+-----+
                             |          |
              +--------------+          +--------------+
              v                                        v
    +-------------------+                     +-------------------+
    |  FastAPI backend   |                     |  React SPA (nginx) |
    |  :8000             |<---- REST/JSON ----> |  static build      |
    |  - Auth (JWT)      |                     +-------------------+
    |  - RBAC            |
    |  - Alert engine    |
    |  - Report engine   |
    |  - APScheduler     |
    +---+-------+---------+
        |       |
        |       +---> Email (SMTP)  [optional]
        v
  +-------------------+
  |  PostgreSQL 16    |
  |  (relational DB)  |
  +-------------------+
        ^
        | REST/JSON (HTTPS + agent API key)
        |
  +-----+---------------------+---------------------+
  |                           |                     |
  v                           v                     v
+-----------------+   +-----------------+   +-----------------+
| Windows Agent   |   | Windows Agent   |   | Windows Agent   |
| (Computer Lab 1)|   | (Admin Office)  |   |  (Library)      |
| - psutil        |   | - psutil        |   | - psutil        |
| - winreg        |   | - winreg        |   | - winreg        |
| - SQLite buffer |   | - SQLite buffer |   | - SQLite buffer |
+-----------------+   +-----------------+   +-----------------+
```

## Components

### 1. FastAPI Backend (`backend/`)
The central API server. Responsibilities:
- **Authentication & RBAC**: JWT access/refresh tokens, bcrypt password hashing,
  role-based access control (system_admin, ict_technician, school_management).
- **Asset management**: computer registration, locations, departments.
- **Monitoring ingestion**: receives heartbeats, hardware metrics, network metrics,
  and software inventory from agents.
- **Alert engine**: evaluates metrics against configurable thresholds, deduplicates
  active alerts, auto-creates incidents for critical conditions, emits recovery
  notifications.
- **Licence management**: tracks software licences, computes days-to-expiry, sends
  reminders at 30/14/7/0 days.
- **Incident & maintenance management**: full lifecycle tracking.
- **Reporting**: generates PDF (ReportLab), Excel (openpyxl), and CSV reports.
- **Audit logging**: records all significant administrative actions.
- **Background workers**: APScheduler runs four jobs (alert evaluation, offline
  detection, licence expiry check, data pruning).

### 2. PostgreSQL Database (`database/`)
A normalised relational schema with ~17 tables. See `database-design.md` for the full
schema. Uses foreign keys, indexes on hot query paths, and cascade rules. Alembic
manages migrations.

### 3. React Frontend (`frontend/`)
A Single Page Application built with React 18, TypeScript, Vite, and Tailwind CSS.
Connects to the backend over REST/JSON. Uses TanStack Query for server state with
auto-refresh on monitoring pages, and Recharts for visualisations. JWT stored in
session memory (access token) and localStorage (refresh token only).

### 4. Windows Monitoring Agent (`monitoring-agent/`)
A Python application installed as a Windows service on every monitored computer.
Collects hardware metrics (psutil), installed software (Windows Registry, not
Win32_Product), and network status. Sends data to the backend over HTTPS using a
unique per-agent API key. Buffers failed transmissions in a local SQLite queue and
retries with exponential backoff when the server is unreachable.

### 5. Notification & Reporting Engines
The notification engine creates in-dashboard notifications for all significant events
and optionally sends email via configurable SMTP. The reporting engine produces
downloadable PDF/Excel/CSV reports for nine report types.

## Data Flow

1. Agent starts with Windows, authenticates with its API key, and begins sending
   heartbeats every 60 seconds (configurable).
2. Each heartbeat carries hardware metrics (CPU, RAM, disk, uptime, temperature where
   available) and network metrics (latency, packet loss, interface status).
3. The backend stores metrics and runs the alert evaluation job (every 60s) which
   compares latest metrics against thresholds.
4. Threshold breaches create or update alerts (deduplicated). Critical alerts
   auto-create incidents and notify administrators.
5. The offline detection job (every 5 min) marks computers as offline if no heartbeat
   arrived within the configured timeout.
6. The licence expiry job (daily 08:00) checks licences approaching expiry and sends
   reminders at configured thresholds.
7. The dashboard reads aggregated data from the API; the frontend further aggregates
   stats client-side (no dedicated stats endpoint).
8. Administrators download reports; the report engine queries the DB and renders
   PDF/Excel/CSV on demand.

## Security Model

- All API endpoints (except login, refresh, health) require a valid JWT.
- Role-based access control enforced on the backend per endpoint.
- Agents authenticate with a unique, hashed API key (shown once at generation).
- Passwords hashed with bcrypt; JWTs signed with HS256 using `SECRET_KEY`.
- CORS restricted to the configured frontend URL.
- Rate limiting on the login endpoint (10/minute) via slowapi.
- Audit logging on all write operations.
- Sensitive values (licence keys, SMTP passwords) are stored as references / encrypted
  and never returned in full by the API.

## Network Topology

The system runs on the school's local network. The backend, database, and nginx proxy
run on a central server. Agents reach the backend via the nginx reverse proxy
(`http://<server>/api/`). No internet/cloud connectivity is required for core
operation; SMTP email is the only optional outbound dependency.
