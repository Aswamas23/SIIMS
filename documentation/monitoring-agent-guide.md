# SIIMS — Monitoring Agent Guide

## Overview

The SIIMS monitoring agent is a small Python application that runs as a Windows
service on each monitored computer. It collects hardware metrics, installed software,
and network status, then reports to the central SIIMS server.

## Prerequisites (target computer)

- Windows 10/11 or Windows Server 2016+
- Python 3.11+
- Network access to the SIIMS server (`http://<server-ip>/api/`)
- Local administrator rights to install the service

## Step 1 — Register the computer in SIIMS

1. Log into the SIIMS dashboard as **System Administrator**.
2. Go to **Computers → Add Computer**.
3. Enter the **hostname** exactly as it appears on the target computer
   (`hostname` in PowerShell). Fill in IP, MAC, OS, and location if known.
4. Save. The computer now appears in the list.
5. Click the computer's **View** button, then click **Generate Agent Key**.
6. **Copy the API key immediately** — it is only shown once.

## Step 2 — Prepare the agent on the target computer

1. Copy the entire `monitoring-agent/` folder onto the target computer
   (e.g. `C:\SIIMSAgent\`).
2. Open PowerShell as Administrator.
3. Install dependencies:
   ```powershell
   cd C:\SIIMSAgent
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Step 3 — Configure the agent

1. Copy `config.ini.example` to `config.ini`.
2. Edit `config.ini`:
   ```ini
   [server]
   url = http://<SIIMS-server-ip>/api
   api_key = <paste-the-api-key-from-step-1>
   computer_id = <the-computer-id-shown-in-the-dashboard>

   [agent]
   heartbeat_interval_seconds = 60
   software_scan_interval_hours = 6
   log_level = INFO
   ```

## Step 4 — Test connectivity

Before installing as a service, verify the agent can reach the server:
```powershell
python agent.py --test
```
You should see a "Heartbeat sent successfully" message. If it fails, check:
- `server.url` is correct and reachable from this computer.
- The SIIMS server is running.
- Windows Firewall allows outbound traffic to the server IP/port.

## Step 5 — Install as a Windows service

```powershell
python install_service.py install
python install_service.py start
```

The service is named **SIIMSAgent** and starts automatically with Windows.

### Manage the service
```powershell
python install_service.py stop       # stop
python install_service.py start      # start
python install_service.py restart   # restart
python install_service.py remove     # uninstall
```

You can also manage it from `services.msc` (the standard Windows Services console).

## Step 6 — Verify in the dashboard

Within 2 minutes, the computer should show status **Online** in the SIIMS dashboard.
Hardware metrics should begin appearing on the computer's detail page.

## Building a standalone executable (optional)

For deployment without a Python installation, build a single .exe with PyInstaller:

```powershell
pip install pyinstaller
pyinstaller --onefile --name siims-agent ^
  --hidden-import win32timezone ^
  --hidden-import win32api ^
  --add-data "config.ini.example;." ^
  agent.py
```
The executable appears in `dist/siims-agent.exe`. Distribute it with a `config.ini`.

## What the agent collects

- **Hardware**: CPU utilisation, CPU temperature (where exposed), RAM utilisation,
  disk utilisation, disk SMART status (where supported), system uptime, battery
  status (laptops).
- **Software**: installed programs discovered via the Windows Registry
  (`HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall` and the WOW6432Node
  equivalent). The agent does **not** use `Win32_Product` (slow and has side effects).
- **Network**: interface status, IP address, gateway reachability, DNS resolution,
  server reachability, latency, packet loss.

## What the agent does NOT collect

The agent monitors computer health and authorised ICT asset information only. It does
not monitor personal activities, capture keystrokes, record screens, or collect
personal files. See the project README "Security & Privacy" section.

## Local queue & offline behaviour

If the SIIMS server is unreachable, the agent buffers metrics in a local SQLite queue
(`siims_queue.db`) and replays them when connectivity is restored. Buffer records
are pruned after 7 days. This ensures no data is lost during network interruptions.

## Log files

Agent logs are written to:
`%APPDATA%\SIIMSAgent\logs\siims_agent.log`

Increase `log_level` to `DEBUG` in `config.ini` for detailed troubleshooting output.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| "Computer stays offline" | Agent not running or wrong server URL | Check service status in `services.msc`; verify `config.ini` `server.url` |
| "Authentication failed" | Wrong/expired API key | Regenerate the agent key in the dashboard, update `config.ini` |
| "Connection refused" | Server down or firewall blocking | Verify backend is up; check server firewall rules |
| "Software inventory empty" | Agent can't read registry | Run the service as LocalSystem (default) |
| "Metrics show as N/A" | Hardware doesn't expose the value | Some metrics (CPU temp, SMART) are hardware-dependent and may be unavailable |
