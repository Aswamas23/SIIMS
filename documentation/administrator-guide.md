# SIIMS — Administrator Guide

For **System Administrators** responsible for configuring and maintaining SIIMS.

## Logging In

Log in with the admin account created during installation (the `ADMIN_EMAIL` /
`ADMIN_PASSWORD` from `.env`). Change your password after first login via the
header dropdown → Profile.

## User Management (Users page)

- Create accounts for ICT technicians and school management staff.
- Assign roles:
  - **System Administrator** — full access.
  - **ICT Technician** — view everything, manage incidents and maintenance.
  - **School Management** — read-only dashboard and reports.
- Use **Reset Password** to issue a temporary password (shown once); instruct the
  user to change it on first login.
- Deactivate (do not delete) users who leave — this preserves audit history.

## Computer Registration (Computers page)

1. Click **Add Computer** and enter the hostname (must match the target machine's
   Windows hostname).
2. Fill optional fields (IP, MAC, manufacturer, model, processor, RAM, storage,
   OS, location, department).
3. Save, then open the computer's detail page and click **Generate Agent Key**.
4. Copy the key and follow the **Monitoring Agent Guide** to install the agent on
   the target computer.
5. The computer shows **Online** once its agent sends the first heartbeat.
6. Deactivate (not delete) retired computers to preserve their history.

## Locations

Manage locations (Computer Lab 1, Admin Office, Library, etc.) via the API or
the Locations endpoints. Assign computers to locations for filtering and reporting.

## Monitoring Thresholds (Settings → Thresholds)

Configure when SIIMS raises warnings:
- CPU warning % (default 90)
- RAM warning % (default 90)
- Disk warning % (default 90) and disk critical % (default 95)
- Offline timeout minutes (default 10) — how long without a heartbeat before a
  computer is marked offline.

The alert engine deduplicates, so a sustained high-CPU condition raises one alert,
not one per heartbeat. Recovery notifications fire automatically when the condition
clears.

## Licence Management (Licences page)

1. **Add Licence** and enter software name, vendor, type (per-seat / site /
   subscription), seats, purchase date, and expiry date.
2. Use **Assign** to attach a licence to one or more computers.
3. SIIMS auto-calculates days remaining and sends reminders at 30 / 14 / 7 days
   before expiry and on the expiry date (via the daily licence job).
4. Licence keys are stored as sensitive references — never displayed in full after
   entry.

Note: detecting installed software does **not** verify its licence. SIIMS tracks
licences you register; it does not auto-detect licence validity unless a software
vendor exposes a supported API (future integration).

## Incident Management

- Incidents are auto-created for critical alerts (e.g. disk critical, computer
  offline beyond timeout).
- Technicians and admins can also create incidents manually.
- Assign incidents to technicians, add investigation notes, update severity, and
  record resolution details. The full update timeline is preserved.
- Duplicate incidents for the same unresolved condition are prevented.

## Maintenance Scheduling (Maintenance page)

- Schedule preventive maintenance per computer (date, type, technician, cost).
- The calendar view shows upcoming work for the current month.
- Mark records complete with completion notes.

## Report Generation (Reports page)

Nine report types are available: Computer Inventory, Hardware Health, Network
Availability, Software Inventory, Software Licences, Incidents, Maintenance,
Computer Downtime, and a summary. Filter by date range and location where
applicable, then download as PDF, Excel, or CSV.

## System Settings

- **General**: school name, system name, timezone.
- **Thresholds**: monitoring thresholds (see above).
- **Email**: SMTP configuration and a "Send Test Email" button.
- **Notifications**: toggle which events generate notifications.
- **Data Retention**: how long to keep metrics and audit logs.

## Audit Logs

Every significant action (user changes, licence changes, incident updates, asset
changes, configuration changes, logins) is recorded with user, action, entity,
IP, and timestamp. Filter by user, action, entity type, and date range.

## Backup

Run a daily `pg_dump` of the PostgreSQL database (see the Installation Guide).
Store backups off the server. Test restoration periodically.

## Performance & Scalability

SIIMS is designed for ~40 computers initially and scales to ~200 without redesign:
- Metrics tables are indexed on (computer_id, recorded_at).
- The dashboard uses latest-metric-per-computer queries (subquery + join) rather
  than scanning full history.
- The data retention job prunes old metrics to bound table growth.
- Agents buffer locally and retry, so network blips don't lose data.
