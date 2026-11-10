"""
Hardware metrics collection for SIIMS Monitoring Agent.
Uses psutil for cross-platform metrics and WMI via PowerShell subprocess
for Windows-specific metrics (CPU temperature, SMART disk health).

All metrics are collected independently — a failure in one metric never
prevents collection of the others. Unavailable metrics are returned as None.
"""
import json
import logging
import subprocess
import sys
import time

import psutil

logger = logging.getLogger(__name__)


def _get_cpu_percent() -> float | None:
    """Return CPU utilisation percentage (1-second sample)."""
    try:
        return psutil.cpu_percent(interval=1)
    except Exception as e:
        logger.warning("Could not collect CPU percent: %s", e)
        return None


def _get_ram_metrics() -> dict:
    """Return RAM utilisation metrics."""
    result = {
        "ram_percent": None,
        "ram_used_gb": None,
        "ram_total_gb": None,
    }
    try:
        mem = psutil.virtual_memory()
        result["ram_percent"] = mem.percent
        result["ram_used_gb"] = round(mem.used / (1024 ** 3), 2)
        result["ram_total_gb"] = round(mem.total / (1024 ** 3), 2)
    except Exception as e:
        logger.warning("Could not collect RAM metrics: %s", e)
    return result


def _get_disk_metrics() -> dict:
    """Return disk utilisation metrics for the primary partition."""
    result = {
        "disk_percent": None,
        "disk_used_gb": None,
        "disk_total_gb": None,
        "disk_free_gb": None,
    }
    try:
        # Use C:\ on Windows, / elsewhere
        path = "C:\\" if sys.platform == "win32" else "/"
        usage = psutil.disk_usage(path)
        result["disk_percent"] = usage.percent
        result["disk_used_gb"] = round(usage.used / (1024 ** 3), 2)
        result["disk_total_gb"] = round(usage.total / (1024 ** 3), 2)
        result["disk_free_gb"] = round(usage.free / (1024 ** 3), 2)
    except Exception as e:
        logger.warning("Could not collect disk metrics: %s", e)
    return result


def _get_uptime_seconds() -> float | None:
    """Return system uptime in seconds."""
    try:
        return round(time.time() - psutil.boot_time(), 1)
    except Exception as e:
        logger.warning("Could not collect uptime: %s", e)
        return None


def _get_cpu_temperature() -> float | None:
    """
    Return CPU temperature in Celsius.
    
    On Linux/macOS: uses psutil.sensors_temperatures() if available.
    On Windows: queries MSAcpi_ThermalZoneTemperature via PowerShell/WMI.
    Returns None if temperature cannot be retrieved on the current platform.
    """
    # Try psutil sensors first (works on Linux with lm-sensors)
    try:
        sensors = psutil.sensors_temperatures()
        if sensors:
            # Try common sensor names in priority order
            for key in ("coretemp", "cpu_thermal", "k10temp", "acpitz"):
                if key in sensors and sensors[key]:
                    return round(sensors[key][0].current, 1)
    except AttributeError:
        # psutil.sensors_temperatures() not available on this platform
        pass
    except Exception as e:
        logger.warning("psutil sensors_temperatures error: %s", e)

    # Windows: query WMI thermal zone via PowerShell
    if sys.platform != "win32":
        return None

    try:
        cmd = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            (
                "try { "
                "$t = Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace root/wmi "
                "-ErrorAction Stop | Select-Object -First 1; "
                "if ($t) { [math]::Round(($t.CurrentTemperature - 2732) / 10.0, 1) } "
                "else { 'unavailable' } "
                "} catch { 'unavailable' }"
            ),
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout.strip()
        if output and output != "unavailable":
            return float(output)
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError) as e:
        logger.warning("Could not collect CPU temperature via WMI: %s", e)
    except Exception as e:
        logger.warning("Unexpected error collecting CPU temperature: %s", e)

    return None


def _get_smart_status() -> str:
    """
    Return SMART disk health status: 'healthy', 'warning', or 'unavailable'.
    Uses PowerShell to query MSStorageDriver_FailurePredictStatus via WMI.
    Only meaningful on Windows — returns 'unavailable' on other platforms.
    """
    if sys.platform != "win32":
        return "unavailable"

    try:
        cmd = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            (
                "try { "
                "$s = Get-WmiObject -Namespace root\\wmi "
                "-Class MSStorageDriver_FailurePredictStatus "
                "-ErrorAction Stop | "
                "Select-Object InstanceName, PredictFailure | "
                "ConvertTo-Json -Depth 2; "
                "if ($s) { $s } else { '[]' } "
                "} catch { '[]' }"
            ),
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = result.stdout.strip()
        if not output or output == "[]":
            return "unavailable"

        # PowerShell may return a single object (dict) or array
        data = json.loads(output)
        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            return "unavailable"

        for entry in data:
            if isinstance(entry, dict):
                predict_failure = entry.get("PredictFailure", False)
                if predict_failure:
                    return "warning"

        return "healthy"

    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        logger.warning("Could not collect SMART status: %s", e)
    except Exception as e:
        logger.warning("Unexpected error collecting SMART status: %s", e)

    return "unavailable"


def _get_battery_info() -> dict | None:
    """
    Return battery info for laptops: percent, is_charging, time_left_seconds.
    Returns None if no battery is present or if data is unavailable.
    """
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return None
        return {
            "percent": round(battery.percent, 1),
            "is_charging": battery.power_plugged,
            "time_left_seconds": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None,
        }
    except AttributeError:
        # sensors_battery() not available on this platform
        return None
    except Exception as e:
        logger.warning("Could not collect battery info: %s", e)
        return None


def collect_hardware_metrics() -> dict:
    """
    Collect all hardware metrics from the local machine.
    
    Every metric is collected independently. Unavailable metrics are None,
    not omitted from the dict. This function never raises.
    
    Returns:
        dict with keys:
            cpu_percent, ram_percent, ram_used_gb, ram_total_gb,
            disk_percent, disk_used_gb, disk_total_gb, disk_free_gb,
            uptime_seconds, cpu_temperature_celsius, smart_status, battery
    """
    metrics = {}

    # CPU
    metrics["cpu_percent"] = _get_cpu_percent()

    # RAM
    metrics.update(_get_ram_metrics())

    # Disk
    metrics.update(_get_disk_metrics())

    # Uptime
    metrics["uptime_seconds"] = _get_uptime_seconds()

    # CPU temperature (Windows WMI or Linux sensors)
    metrics["cpu_temperature_celsius"] = _get_cpu_temperature()

    # SMART disk health
    metrics["smart_status"] = _get_smart_status()

    # Battery (laptops only)
    metrics["battery"] = _get_battery_info()

    return metrics


if __name__ == "__main__":
    import pprint
    logging.basicConfig(level=logging.INFO)
    print("Collecting hardware metrics...")
    result = collect_hardware_metrics()
    pprint.pprint(result)
