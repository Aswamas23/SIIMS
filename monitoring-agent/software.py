"""
Software inventory collection for SIIMS Monitoring Agent.
Scans the Windows registry for installed software.

IMPORTANT: Never use Win32_Product (triggers MSI reconfiguration).
Uses winreg (stdlib on Windows) wrapped in try/except ImportError
so this module can be imported on non-Windows systems for testing.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# winreg is Windows-only; guard import so tests can run on Linux/macOS CI
try:
    import winreg as _winreg
    _WINREG_AVAILABLE = True
except ImportError:
    _winreg = None  # type: ignore[assignment]
    _WINREG_AVAILABLE = False


# Registry paths that contain installed software records
_UNINSTALL_PATHS = [
    # 64-bit applications
    (None, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    # 32-bit applications on 64-bit Windows
    (None, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    # Per-user installations
    ("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
]


def _parse_install_date(raw: str | None) -> str | None:
    """
    Convert YYYYMMDD registry string to ISO date format YYYY-MM-DD.
    Returns None if the value is missing or malformed.
    """
    if not raw:
        return None
    raw = raw.strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return None


def _read_string_value(key: Any, value_name: str) -> str | None:
    """
    Safely read a string value from an open registry key.
    Returns None if the value does not exist or is not a string.
    """
    try:
        value, reg_type = _winreg.QueryValueEx(key, value_name)
        # REG_SZ = 1, REG_EXPAND_SZ = 2
        if reg_type in (1, 2) and isinstance(value, str):
            return value.strip() or None
        return None
    except (OSError, FileNotFoundError):
        return None


def _scan_registry_path(hive_const: int, subkey_path: str) -> list[dict]:
    """
    Enumerate all subkeys under the given registry path and extract
    software information from each one.
    
    Returns a list of dicts with name, publisher, version, install_date.
    """
    entries = []
    try:
        hive = _winreg.OpenKey(hive_const, subkey_path)
    except (OSError, FileNotFoundError) as e:
        logger.debug("Registry path not accessible %s\\%s: %s", hive_const, subkey_path, e)
        return entries

    try:
        index = 0
        while True:
            try:
                subkey_name = _winreg.EnumKey(hive, index)
            except OSError:
                # No more subkeys
                break

            index += 1

            try:
                subkey = _winreg.OpenKey(hive, subkey_name)
                try:
                    name = _read_string_value(subkey, "DisplayName")
                    if not name:
                        # Skip entries without a display name
                        continue

                    publisher = _read_string_value(subkey, "Publisher")
                    version = _read_string_value(subkey, "DisplayVersion")
                    install_date_raw = _read_string_value(subkey, "InstallDate")
                    install_date = _parse_install_date(install_date_raw)

                    entries.append({
                        "name": name,
                        "publisher": publisher,
                        "version": version,
                        "install_date": install_date,
                    })
                finally:
                    _winreg.CloseKey(subkey)
            except Exception as e:
                logger.debug("Error reading registry subkey %s: %s", subkey_name, e)
                continue
    finally:
        _winreg.CloseKey(hive)

    return entries


def _deduplicate(entries: list[dict]) -> list[dict]:
    """
    Deduplicate software entries by (name, publisher, version).
    Preserves the first occurrence of each unique combination.
    """
    seen: set[tuple] = set()
    unique = []
    for entry in entries:
        key = (
            (entry.get("name") or "").lower(),
            (entry.get("publisher") or "").lower(),
            (entry.get("version") or "").lower(),
        )
        if key not in seen:
            seen.add(key)
            unique.append(entry)
    return unique


def collect_software() -> list[dict]:
    """
    Scan the Windows registry for installed software.
    
    Scans three registry locations:
    - HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall
    - HKLM\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall
    - HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall
    
    Returns:
        List of dicts, each with keys: name, publisher, version, install_date.
        Returns an empty list if winreg is unavailable or on any failure.
    
    Note:
        Never uses Win32_Product to avoid triggering MSI reconfiguration.
    """
    if not _WINREG_AVAILABLE:
        logger.warning("winreg not available (non-Windows platform); returning empty software list")
        return []

    all_entries: list[dict] = []

    hive_map = {
        None: _winreg.HKEY_LOCAL_MACHINE,
        "HKCU": _winreg.HKEY_CURRENT_USER,
    }

    try:
        for hive_key, subkey_path in _UNINSTALL_PATHS:
            hive_const = hive_map.get(hive_key, _winreg.HKEY_LOCAL_MACHINE)
            try:
                entries = _scan_registry_path(hive_const, subkey_path)
                all_entries.extend(entries)
            except Exception as e:
                logger.warning("Failed to scan registry path %s: %s", subkey_path, e)

        deduplicated = _deduplicate(all_entries)
        logger.info("Software inventory: found %d unique entries", len(deduplicated))
        return deduplicated

    except Exception as e:
        logger.error("Software collection failed entirely: %s", e)
        return []


if __name__ == "__main__":
    import pprint
    logging.basicConfig(level=logging.INFO)
    print("Collecting software inventory...")
    result = collect_software()
    print(f"Found {len(result)} installed applications:")
    pprint.pprint(result[:10])  # Show first 10 for brevity
