"""
Configuration management for SIIMS Monitoring Agent.
Reads config.ini from the same directory as the script (or executable in PyInstaller mode).
"""
import configparser
import os
import sys
from dataclasses import dataclass

_PLACEHOLDER_API_KEY = "YOUR_API_KEY_HERE"


@dataclass
class Config:
    """Agent configuration dataclass."""
    # Server settings
    server_url: str
    api_key: str
    computer_id: int

    # Agent settings
    heartbeat_interval_seconds: int
    software_scan_interval_hours: int
    log_level: str
    log_file: str
    queue_db: str
    max_queue_age_days: int
    retry_attempts: int


def _find_config_file() -> str:
    """
    Locate config.ini relative to the script or PyInstaller executable.
    
    Search order:
    1. Same directory as __file__ (normal Python execution)
    2. os.path.dirname(sys.executable) (PyInstaller one-file mode)
    3. Current working directory as a fallback
    """
    candidates = []

    # Normal Python: beside the script file
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidates.append(os.path.join(script_dir, "config.ini"))
    except NameError:
        pass

    # PyInstaller one-file: beside the extracted executable
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    candidates.append(os.path.join(exe_dir, "config.ini"))

    # Fallback: current working directory
    candidates.append(os.path.join(os.getcwd(), "config.ini"))

    for path in candidates:
        if os.path.isfile(path):
            return path

    raise FileNotFoundError(
        "config.ini not found. Expected locations:\n"
        + "\n".join(f"  {c}" for c in candidates)
        + "\n\nCopy config.ini.example to config.ini and fill in your settings."
    )


def load_config(config_path: str = None) -> Config:
    """
    Load and validate configuration from config.ini.
    
    Args:
        config_path: Optional explicit path to config.ini (used in tests)
    
    Returns:
        Populated Config dataclass
    
    Raises:
        FileNotFoundError: If config.ini cannot be located
        ValueError: If required fields are missing or still have placeholder values
    """
    if config_path is None:
        config_path = _find_config_file()

    parser = configparser.ConfigParser()
    read_files = parser.read(config_path, encoding="utf-8")
    if not read_files:
        raise FileNotFoundError(f"Could not read config file: {config_path}")

    # --- Validate [server] section ---
    if not parser.has_section("server"):
        raise ValueError("config.ini is missing the [server] section")

    api_key = parser.get("server", "api_key", fallback="").strip()
    if not api_key:
        raise ValueError("api_key is missing in [server] section of config.ini")
    if api_key == _PLACEHOLDER_API_KEY:
        raise ValueError(
            "api_key is still set to the placeholder value. "
            "Replace YOUR_API_KEY_HERE with the actual agent API key."
        )

    server_url = parser.get("server", "url", fallback="").strip().rstrip("/")
    if not server_url:
        raise ValueError("url is missing in [server] section of config.ini")

    try:
        computer_id = parser.getint("server", "computer_id", fallback=0)
    except ValueError:
        raise ValueError("computer_id in [server] must be an integer")

    # --- Validate [agent] section ---
    if not parser.has_section("agent"):
        raise ValueError("config.ini is missing the [agent] section")

    try:
        heartbeat_interval_seconds = parser.getint("agent", "heartbeat_interval_seconds", fallback=60)
    except ValueError:
        raise ValueError("heartbeat_interval_seconds in [agent] must be an integer")

    try:
        software_scan_interval_hours = parser.getint("agent", "software_scan_interval_hours", fallback=6)
    except ValueError:
        raise ValueError("software_scan_interval_hours in [agent] must be an integer")

    log_level = parser.get("agent", "log_level", fallback="INFO").strip().upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level not in valid_levels:
        raise ValueError(f"log_level must be one of {valid_levels}, got: {log_level!r}")

    log_file = parser.get("agent", "log_file", fallback="siims_agent.log").strip()
    queue_db = parser.get("agent", "queue_db", fallback="siims_queue.db").strip()

    try:
        max_queue_age_days = parser.getint("agent", "max_queue_age_days", fallback=7)
    except ValueError:
        raise ValueError("max_queue_age_days in [agent] must be an integer")

    try:
        retry_attempts = parser.getint("agent", "retry_attempts", fallback=3)
    except ValueError:
        raise ValueError("retry_attempts in [agent] must be an integer")

    return Config(
        server_url=server_url,
        api_key=api_key,
        computer_id=computer_id,
        heartbeat_interval_seconds=heartbeat_interval_seconds,
        software_scan_interval_hours=software_scan_interval_hours,
        log_level=log_level,
        log_file=log_file,
        queue_db=queue_db,
        max_queue_age_days=max_queue_age_days,
        retry_attempts=retry_attempts,
    )


if __name__ == "__main__":
    try:
        config = load_config()
        print("Config loaded successfully:")
        print(f"  Server URL:                 {config.server_url}")
        print(f"  Computer ID:                {config.computer_id}")
        print(f"  API Key:                    {'*' * len(config.api_key)}")
        print(f"  Heartbeat interval:         {config.heartbeat_interval_seconds}s")
        print(f"  Software scan interval:     {config.software_scan_interval_hours}h")
        print(f"  Log level:                  {config.log_level}")
        print(f"  Log file:                   {config.log_file}")
        print(f"  Queue DB:                   {config.queue_db}")
        print(f"  Max queue age (days):       {config.max_queue_age_days}")
        print(f"  Retry attempts:             {config.retry_attempts}")
    except (FileNotFoundError, ValueError) as e:
        print(f"Config error: {e}")
        sys.exit(1)
