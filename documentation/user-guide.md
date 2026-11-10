# SIIMS — User Guide

For **ICT Technicians** and **School Management** staff using SIIMS.

## Logging In

Open the SIIMS URL in your browser and log in with the email and password your
administrator gave you. If you received a temporary password, change it from the
header dropdown → Profile after logging in.

Your role determines what you can see and do.

---

## ICT Technician

Technicians can view all monitoring data, manage incidents, and record maintenance.
You cannot manage users, locations, or system settings.

### Dashboard
The dashboard gives an at-a-glance overview: how many computers are online/offline,
how many have warnings, how many critical incidents are open, and how many licences
are expiring. Charts show CPU/RAM/disk usage across computers. Use it to spot
problems quickly.

### Computers
Browse all registered computers. Filter by status (online/offline/warning) or
location. Click a computer to see its full detail: hardware specs, live metrics with
trend charts, installed software, network status, incident history, and maintenance
history.

### Hardware Monitoring
A live table of all computers' current CPU, RAM, and disk usage with colour-coded
bars. Red means a threshold is breached. Auto-refreshes every 30 seconds.

### Network Monitoring
Shows each computer's network status, latency, and packet loss. Offline computers
are highlighted. Auto-refreshes every 60 seconds.

### Software Inventory
Two views:
- **By Computer**: pick a computer to see what's installed.
- **By Software**: see which software is installed across the school and how many
  computers have each.

### Incidents (your main workflow)
1. Open **Incidents** to see all open and in-progress items.
2. Filter by status, severity, or search.
3. Click an incident to open its detail. You'll see the description, severity,
   status, and a timeline of all updates.
4. **Assign** it to yourself (or another technician).
5. **Add notes** as you investigate (each note is timestamped and preserved).
6. When fixed, click **Mark Resolved** and enter resolution notes.
7. An administrator will close it after review.

You can also **Report Incident** manually if you notice a problem the system hasn't
flagged.

### Maintenance
View scheduled and completed maintenance. Use **Schedule** to create a new
maintenance record (pick the computer, type, date, and description). When work is
done, click **Mark Complete** with completion notes.

### Reports
Download reports (Computer Inventory, Hardware Health, Network, Software, Licences,
Incidents, Maintenance, Downtime) as PDF, Excel, or CSV. Useful for monthly
summaries or audits.

---

## School Management

School Management users have **read-only** access. You can view the dashboard,
computer availability, incident summaries, licence expiry reports, and performance
and maintenance reports — but you cannot change anything.

### Dashboard
Use the dashboard to understand the overall health of the school's ICT
infrastructure at a high level: how many computers are working, how many have
issues, how many incidents are open, and which licences need renewing soon.

### Reports
The Reports page is the most useful section for management. Download:
- **Computer Inventory** — what hardware the school owns.
- **Incidents** — what's gone wrong and how it was resolved.
- **Software Licences** — what's expiring and needs budget for renewal.
- **Maintenance** — what servicing has been done.
- **Computer Downtime** — which computers were unavailable and for how long.

Filter by date range to report on a specific term or month.

### Incidents (view only)
You can view incidents to understand recurring problems, but only technicians
and admins can update them.

---

## Tips

- The notification bell in the top-right shows alerts and reminders. Click it to
  review and dismiss notifications.
- Monitoring pages auto-refresh, so you can leave them open on a spare screen.
- If a computer shows **Offline** but you know it's on, check with the technician —
  the agent service may have stopped or the network may be down.
- Use the search box on list pages to find a specific computer or software name.
