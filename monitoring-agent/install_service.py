"""
SIIMS Agent service installer/manager.
Provides install, uninstall, start, stop, and status commands.
Must be run with administrator privileges.
"""
import argparse
import ctypes
import os
import shutil
import sys

# Guard pywin32 imports — service management is Windows-only
try:
    import win32service
    import win32serviceutil
    _WIN32_AVAILABLE = True
except ImportError:
    win32service = None        # type: ignore[assignment]
    win32serviceutil = None    # type: ignore[assignment]
    _WIN32_AVAILABLE = False


SERVICE_NAME = "SIIMSAgent"
SERVICE_DISPLAY_NAME = "SIIMS Monitoring Agent"


def _require_windows() -> None:
    """Exit with an error message if not on Windows."""
    if not _WIN32_AVAILABLE:
        print("ERROR: This script requires Windows with pywin32 installed.")
        sys.exit(1)


def _require_admin() -> None:
    """Exit with an error message if the process is not elevated."""
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False

    if not is_admin:
        print("ERROR: Administrator privileges are required to manage Windows services.")
        print("Please right-click and select 'Run as administrator', or use an elevated PowerShell prompt.")
        sys.exit(1)


def _get_script_path() -> str:
    """Return the absolute path to agent.py (resolved relative to this script)."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "agent.py")


def cmd_install(config_path: str | None = None) -> None:
    """Install the SIIMS Agent Windows service."""
    _require_windows()
    _require_admin()

    agent_script = _get_script_path()
    if not os.path.isfile(agent_script):
        print(f"ERROR: agent.py not found at {agent_script}")
        sys.exit(1)

    # If a config path is provided, copy it to the service directory
    if config_path:
        if not os.path.isfile(config_path):
            print(f"ERROR: Config file not found: {config_path}")
            sys.exit(1)
        dest = os.path.join(os.path.dirname(agent_script), "config.ini")
        shutil.copy2(config_path, dest)
        print(f"Copied config to: {dest}")

    try:
        win32serviceutil.InstallService(
            pythonClassString=f"agent.SIIMSAgentService",
            serviceName=SERVICE_NAME,
            displayName=SERVICE_DISPLAY_NAME,
            startType=win32service.SERVICE_AUTO_START,
            exeName=sys.executable,
        )
        print(f"Service '{SERVICE_DISPLAY_NAME}' installed successfully.")
        print("Use 'python install_service.py start' to start the service.")
    except Exception as e:
        print(f"ERROR: Failed to install service: {e}")
        sys.exit(1)


def cmd_uninstall() -> None:
    """Uninstall the SIIMS Agent Windows service."""
    _require_windows()
    _require_admin()

    # Stop first if running
    try:
        win32serviceutil.StopService(SERVICE_NAME)
        print("Service stopped.")
    except Exception:
        pass  # Already stopped or not running

    try:
        win32serviceutil.RemoveService(SERVICE_NAME)
        print(f"Service '{SERVICE_DISPLAY_NAME}' uninstalled successfully.")
    except Exception as e:
        print(f"ERROR: Failed to uninstall service: {e}")
        sys.exit(1)


def cmd_start() -> None:
    """Start the SIIMS Agent Windows service."""
    _require_windows()
    _require_admin()

    try:
        win32serviceutil.StartService(SERVICE_NAME)
        print(f"Service '{SERVICE_DISPLAY_NAME}' started.")
    except Exception as e:
        print(f"ERROR: Failed to start service: {e}")
        sys.exit(1)


def cmd_stop() -> None:
    """Stop the SIIMS Agent Windows service."""
    _require_windows()
    _require_admin()

    try:
        win32serviceutil.StopService(SERVICE_NAME)
        print(f"Service '{SERVICE_DISPLAY_NAME}' stopped.")
    except Exception as e:
        print(f"ERROR: Failed to stop service: {e}")
        sys.exit(1)


def cmd_status() -> None:
    """Print the current status of the SIIMS Agent Windows service."""
    _require_windows()

    status_map = {
        win32service.SERVICE_STOPPED: "STOPPED",
        win32service.SERVICE_START_PENDING: "START_PENDING",
        win32service.SERVICE_STOP_PENDING: "STOP_PENDING",
        win32service.SERVICE_RUNNING: "RUNNING",
        win32service.SERVICE_CONTINUE_PENDING: "CONTINUE_PENDING",
        win32service.SERVICE_PAUSE_PENDING: "PAUSE_PENDING",
        win32service.SERVICE_PAUSED: "PAUSED",
    }

    try:
        status_code = win32serviceutil.QueryServiceStatus(SERVICE_NAME)[1]
        status_text = status_map.get(status_code, f"UNKNOWN ({status_code})")
        print(f"Service '{SERVICE_DISPLAY_NAME}': {status_text}")
    except Exception as e:
        print(f"Could not query service status: {e}")
        print("The service may not be installed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SIIMS Agent Service Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  install   Install the Windows service (requires admin)
  uninstall Remove the Windows service (requires admin)
  start     Start the Windows service (requires admin)
  stop      Stop the Windows service (requires admin)
  status    Show current service status

Examples:
  python install_service.py install --config-path C:\\SIIMS\\config.ini
  python install_service.py start
  python install_service.py status
  python install_service.py stop
  python install_service.py uninstall
""",
    )
    parser.add_argument(
        "command",
        choices=["install", "uninstall", "start", "stop", "status"],
        help="Service management command",
    )
    parser.add_argument(
        "--config-path",
        metavar="PATH",
        default=None,
        help="Path to config.ini to copy to the service directory (install only)",
    )

    args = parser.parse_args()

    command_map = {
        "install": lambda: cmd_install(args.config_path),
        "uninstall": cmd_uninstall,
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
    }

    command_map[args.command]()


if __name__ == "__main__":
    main()
