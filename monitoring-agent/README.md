# SIIMS Monitoring Agent

A standalone Python Windows service that collects hardware metrics, software inventory, and network status from a monitored computer and reports them to the SIIMS central backend via REST API.

---

## Overview

The agent runs as a Windows service and periodically:

1. Collects CPU, RAM, disk, uptime, and temperature metrics (via `psutil` + WMI PowerShell)
2. Checks network connectivity to the backend server (via `subprocess` ping)
3. Sends a **heartbeat payload** to `/api/v1/agents/heartbeat`
4. Runs a **software inventory scan** at a configurable interval (default: every 6 hours) and sends results to `/api/v1/agents/software-inventory`
5. Buffers payloads in a local SQLite queue if the server is unreachable and replays them on reconnection

---

## Requirements

- Windows 10/11 or Windows Server 2016+
- Python 3.11+ (for packaging) or the distributed `.exe`
- Administrator privileges (for service install/uninstall/start/stop)

---

## Installation

### 1. Install Python dependencies

```powershell
pip install -r requirements.txt
```

### 2. Configure the agent

Copy the example config and fill in your values:

```powershell
copy config.ini.example config.ini
notepad config.ini
```

Required settings in `config.ini`:

```ini
[server]
url = http://192.168.1.100:8000      ; Central SIIMS backend URL
api_key = <your-api-key-here>        ; API key from SIIMS admin panel
computer_id = 5                      ; Computer ID assigned in SIIMS

[agent]
heartbeat_interval_seconds = 60
software_scan_interval_hours = 6
log_level = INFO
log_file = siims_agent.log
queue_db = siims_queue.db
max_queue_age_days = 7
retry_attempts = 3
```

> **Never** leave `api_key` as `YOUR_API_KEY_HERE` — the agent will refuse to start.

### 3. Install the Windows service

Open an **elevated** PowerShell prompt:

```powershell
python install_service.py install --config-path C:\SIIMS\config.ini
python install_service.py start
python install_service.py status
```

---

## Service Management Commands

```powershell
# Check service status
python install_service.py status

# Start / stop / restart
python install_service.py start
python install_service.py stop

# Uninstall
python install_service.py uninstall
```

All commands require administrator privileges.

---

## Module Reference

| File | Purpose |
|------|---------|
| `config.py` | Reads and validates `config.ini` |
| `logger.py` | Rotating file + console logger |
| `hardware.py` | CPU/RAM/disk/temperature/SMART metrics |
| `software.py` | Windows registry software inventory |
| `network.py` | Ping + network interface status |
| `api_client.py` | HTTP client with exponential backoff |
| `local_queue.py` | SQLite offline buffer + replay |
| `heartbeat.py` | Orchestrates collection and transmission |
| `agent.py` | Windows service entry point |
| `install_service.py` | Service installer/manager CLI |

---

## Running Tests

Tests run on any OS — all Windows-specific system calls are mocked.

```powershell
# From the monitoring-agent directory
python -m pytest tests/ -v

# Or from the repository root
python -m pytest monitoring-agent/tests/ -v
```

---

## Building a Standalone Executable

Use PyInstaller to produce a single `.exe` for distribution to monitored computers:

```powershell
pip install pyinstaller==6.6.0

pyinstaller ^
  --onefile ^
  --name SIIMSAgent ^
  --hidden-import win32timezone ^
  --hidden-import win32api ^
  --hidden-import win32service ^
  --hidden-import win32serviceutil ^
  --hidden-import win32event ^
  --add-data "config.ini.example;." ^
  agent.py
```

The resulting `dist\SIIMSAgent.exe` can be distributed to any Windows machine.

After copying the `.exe` to the target machine:

```powershell
# Place config.ini in the same directory as the .exe, then:
SIIMSAgent.exe install
SIIMSAgent.exe start
```

---

## Offline Buffering

If the backend server is unreachable, payloads are saved to a local SQLite database (`siims_queue.db` by default). The agent retries in FIFO order on the next successful heartbeat cycle. Entries older than `max_queue_age_days` (default: 7 days) or with 10+ failed attempts are automatically pruned.

---

## Logging

Logs are written to `siims_agent.log` (configurable) with rotation at 5MB, keeping 3 backups. Output is also written to stdout.

Log location when running as a service: same directory as `agent.py` or `SIIMSAgent.exe`.

---

## Security Notes

- The API key is transmitted as a `Bearer` token over HTTP/HTTPS to the backend.
- Use HTTPS in production (`url = https://...` in `config.ini`) with a valid certificate on the backend.
- The `api_key` value is stored in plaintext in `config.ini` — restrict file permissions appropriately.
- The backend stores only a bcrypt hash of the API key; the plaintext never persists on the server.

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Service fails to start | Check `siims_agent.log`; verify `config.ini` exists and `api_key` is set |
| `ValueError: api_key is still set to the placeholder` | Edit `config.ini` and set a real API key |
| Heartbeats not appearing in dashboard | Check network connectivity; inspect `siims_queue.db` for buffered entries |
| CPU temperature shows `null` | WMI thermal sensor not supported by this hardware/driver |
| SMART status shows `unavailable` | WMI storage driver not installed or not supported |
