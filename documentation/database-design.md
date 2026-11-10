# SIIMS — Database Design

## Overview

SIIMS uses PostgreSQL 16 with a normalised relational schema. Migrations are
managed by Alembic (`backend/migrations/`). The schema has 17 core tables plus one
junction table.

## Entity-Relationship Summary

```
users 1---* refresh_tokens
users 1---* notifications
users 1---* audit_logs
users 1---* incidents (created_by / assigned_to)
users 1---* maintenance_records (performed_by)

locations 1---* computers

computers 1---* agent_credentials
computers 1---* hardware_metrics
computers 1---* network_metrics
computers 1---* installed_software
computers 1---* incidents
computers 1---* maintenance_records
computers 1---* alerts

software_licences 1---* licence_assignments *---1 computers

incidents 1---* incident_updates
alerts 1---1 incidents (related_alert, optional)
```

## Tables

### users
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, autoincrement |
| email | String(255) | UNIQUE, NOT NULL, indexed |
| full_name | String(255) | NOT NULL |
| hashed_password | String(255) | NOT NULL |
| role | Enum(system_admin, ict_technician, school_management) | NOT NULL, default ict_technician |
| is_active | Boolean | NOT NULL, default true |
| phone | String(50) | nullable |
| created_at | DateTime(tz) | NOT NULL |
| updated_at | DateTime(tz) | NOT NULL |
| last_login | DateTime(tz) | nullable |
Indexes: email, role, is_active.

### refresh_tokens
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| user_id | Integer | FK users.id ON DELETE CASCADE, indexed |
| jti | String(36) | UNIQUE, NOT NULL, indexed |
| is_revoked | Boolean | NOT NULL, default false |
| created_at | DateTime(tz) | default now |
| expires_at | DateTime(tz) | NOT NULL |

### locations
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| name | String(255) | NOT NULL, unique |
| description | String | nullable |
| building | String | nullable |
| floor | String | nullable |
| created_at / updated_at | DateTime(tz) | NOT NULL |

### computers
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, indexed |
| hostname | String(255) | NOT NULL, UNIQUE |
| ip_address | String(45) | nullable, indexed |
| mac_address | String(17) | nullable, unique |
| manufacturer / model / processor | String | nullable |
| ram_gb | Integer | nullable |
| storage_gb | BigInteger | nullable |
| operating_system / os_version | String | nullable |
| location_id | Integer | FK locations.id ON DELETE SET NULL, indexed |
| department | String | nullable |
| is_active | Boolean | NOT NULL, default true |
| status | Enum(online, offline, warning, critical, maintenance, unknown) | NOT NULL, default unknown, indexed |
| notes | Text | nullable |
| registered_at | DateTime(tz) | NOT NULL |
| last_seen | DateTime(tz) | nullable, indexed |
| updated_at | DateTime(tz) | NOT NULL |
Composite index: (location_id, status, is_active, last_seen).

### agent_credentials
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| computer_id | Integer | FK computers.id ON DELETE CASCADE |
| key_hash | String | NOT NULL |
| label | String | nullable |
| is_active | Boolean | default true |
| created_at / last_used | DateTime(tz) | nullable |

### hardware_metrics
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| computer_id | Integer | FK computers.id ON DELETE CASCADE, indexed |
| recorded_at | DateTime(tz) | NOT NULL, indexed |
| cpu_percent / cpu_temp_celsius / cpu_freq_mhz | Float | nullable |
| ram_percent / ram_used_gb / ram_total_gb | Float | nullable |
| disk_percent / disk_used_gb / disk_total_gb / disk_free_gb | Float | nullable |
| smart_status | String | nullable |
| uptime_seconds | Integer | nullable |
| battery_percent / battery_plugged | Float/Bool | nullable |
Index: computer_id + recorded_at for latest-metric queries.

### network_metrics
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| computer_id | Integer | FK computers.id ON DELETE CASCADE, indexed |
| recorded_at | DateTime(tz) | NOT NULL, indexed |
| interface_name / ip_address / mac_address | String | nullable |
| is_up / gateway_reachable / dns_resolves / server_reachable | Boolean | nullable |
| latency_ms / packet_loss_percent | Float | nullable |
| bytes_sent / bytes_recv | Integer | nullable |

### installed_software
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| computer_id | Integer | FK computers.id ON DELETE CASCADE, indexed |
| name | String | NOT NULL |
| version / publisher | String | nullable |
| install_date | Date | nullable |
| first_seen / last_seen | DateTime(tz) | NOT NULL |
| is_active | Boolean | default true |

### software_licences
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| software_name | String(500) | NOT NULL, indexed |
| version | String | nullable |
| licence_key | Text | nullable (sensitive — store reference, not raw key) |
| licence_type | String | nullable |
| vendor | String | nullable |
| seats | Integer | nullable |
| purchase_date / expiry_date | Date | nullable, expiry_date indexed |
| cost | Integer | nullable (cents) |
| notes | Text | nullable |
| status | Enum(active, expired, expiring_soon, perpetual, unknown) | NOT NULL, indexed |
| is_active | Boolean | NOT NULL, default true |
| created_at / updated_at | DateTime(tz) | NOT NULL |

### licence_assignments (junction)
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| licence_id | Integer | FK software_licences.id ON DELETE CASCADE |
| computer_id | Integer | FK computers.id ON DELETE CASCADE |
| created_at | DateTime(tz) | NOT NULL |
Unique: (licence_id, computer_id).

### incidents
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| incident_number | String(30) | UNIQUE, NOT NULL, indexed |
| computer_id | Integer | FK computers.id ON DELETE SET NULL, indexed |
| title | String(500) | NOT NULL |
| description | Text | nullable |
| category | Enum(hardware, software, network, security, performance, maintenance, other) | NOT NULL |
| severity | Enum(low, medium, high, critical) | NOT NULL |
| status | Enum(open, in_progress, resolved, closed) | NOT NULL, indexed |
| created_by_id | Integer | FK users.id ON DELETE SET NULL |
| assigned_to_id | Integer | FK users.id ON DELETE SET NULL, indexed |
| is_auto_created | Boolean | default false |
| related_alert_id | Integer | FK alerts.id ON DELETE SET NULL |
| created_at / updated_at / resolved_at | DateTime(tz) | indexed |
| resolution_notes | Text | nullable |

### incident_updates
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| incident_id | Integer | FK incidents.id ON DELETE CASCADE, indexed |
| user_id | Integer | FK users.id ON DELETE SET NULL |
| update_type | Enum(comment, status_change, assignment, resolution) | NOT NULL |
| message | Text | NOT NULL |
| old_status / new_status | String | nullable |
| created_at | DateTime(tz) | NOT NULL, indexed |

### maintenance_records
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| computer_id | Integer | FK computers.id ON DELETE CASCADE, indexed |
| performed_by_id | Integer | FK users.id ON DELETE SET NULL |
| maintenance_type | Enum(preventive, corrective, upgrade, inspection, other) | NOT NULL |
| title | String(500) | NOT NULL |
| description | Text | nullable |
| scheduled_date / completed_date | Date | nullable, indexed |
| cost | Integer | nullable (cents) |
| notes | Text | nullable |
| created_at / updated_at | DateTime(tz) | NOT NULL |

### alerts
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| computer_id | Integer | FK computers.id ON DELETE CASCADE, indexed |
| alert_type | Enum(cpu_high, ram_high, disk_high, disk_critical, smart_failure, computer_offline, network_issue, licence_expiring, licence_expired, battery_low, custom) | NOT NULL, indexed |
| severity | Enum(warning, critical, info) | NOT NULL, indexed |
| status | Enum(active, acknowledged, resolved) | NOT NULL, indexed |
| title | String(500) | NOT NULL |
| message | Text | nullable |
| metric_value / threshold_value | Float | nullable |
| is_acknowledged | Boolean | default false |
| acknowledged_by_id | Integer | FK users.id ON DELETE SET NULL |
| acknowledged_at / resolved_at | DateTime(tz) | nullable |
| created_at / updated_at | DateTime(tz) | indexed |
Composite index: (computer_id, alert_type, status) for deduplication.

### notifications
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| user_id | Integer | FK users.id ON DELETE CASCADE, indexed |
| title | String(500) | NOT NULL |
| message | Text | nullable |
| notification_type | Enum(alert, incident, licence, maintenance, system, info) | NOT NULL |
| related_id | Integer | nullable (generic FK) |
| related_type | String(50) | nullable |
| is_read | Boolean | default false, indexed |
| created_at / read_at | DateTime(tz) | nullable |
Composite index: (user_id, is_read).

### audit_logs
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| user_id | Integer | FK users.id, nullable |
| action | String | NOT NULL |
| entity_type | String | nullable |
| entity_id | Integer | nullable |
| details | JSON | nullable |
| ip_address / user_agent | String | nullable |
| created_at | DateTime(tz) | NOT NULL, indexed |

### system_settings
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| key | String | NOT NULL, unique |
| value | String | nullable |
| value_type | String | NOT NULL (string/integer/float/boolean) |
| description | String | nullable |
| category | String | nullable |
| updated_at | DateTime(tz) | NOT NULL |

## Design Notes

- **Soft deletes**: computers and users use `is_active` rather than hard deletes, so
  historical metrics and audit logs remain intact.
- **Cascade rules**: metrics, software, and alerts cascade-delete with a computer;
  incidents and maintenance use SET NULL so history survives asset removal.
- **Timestamps**: all timestamps are timezone-aware (`DateTime(timezone=True)`).
- **Data retention**: the `prune_data` scheduler job deletes metrics older than
  `data_retention_days` (configurable in Settings).

## Creating the Schema

```bash
cd backend
alembic upgrade head
```
For a fresh database without Alembic, the SQL is available in `database/schema.sql`.
