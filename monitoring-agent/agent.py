"""
SIIMS Monitoring Agent — Windows Service entry point.
Implements win32serviceutil.ServiceFramework to run as a Windows service.

win32serviceutil is imported inside a try/except at module level so this
file can be imported on non-Windows systems (e.g. for unit tests) without
crashing on the missing pywin32 dependency.
"""
import logging
import sys
import threading

# Guard pywin32 imports for cross-platform compatibility
try:
    import win32event
    import win32service
    import win32serviceutil
    _WIN32_AVAILABLE = True
except ImportError:
    win32event = None          # type: ignore[assignment]
    win32service = None        # type: ignore[assignment]
    win32serviceutil = None    # type: ignore[assignment]
    _WIN32_AVAILABLE = False

from api_client import APIClient
from config import load_config
from heartbeat import HeartbeatCollector
from local_queue import LocalQueue
from logger import get_logger

logger = logging.getLogger(__name__)


def _build_components(config_path: str = None):
    """
    Instantiate and wire all agent components from the configuration.
    Returns (config, api_client, local_queue, heartbeat_collector).
    """
    config = load_config(config_path)
    root_logger = get_logger("siims_agent", log_file=config.log_file, log_level=config.log_level)
    root_logger.info("SIIMS Agent starting — computer_id=%d, server=%s", config.computer_id, config.server_url)

    local_queue = LocalQueue(db_path=config.queue_db, max_queue_age_days=config.max_queue_age_days)
    api_client = APIClient(config=config, local_queue=local_queue)
    heartbeat_collector = HeartbeatCollector(config=config, api_client=api_client, local_queue=local_queue)

    return config, api_client, local_queue, heartbeat_collector


# ---------------------------------------------------------------------------
# Windows Service class — only defined when pywin32 is available
# ---------------------------------------------------------------------------

if _WIN32_AVAILABLE:
    class SIIMSAgentService(win32serviceutil.ServiceFramework):
        """Windows service wrapper for the SIIMS monitoring agent."""

        _svc_name_ = "SIIMSAgent"
        _svc_display_name_ = "SIIMS Monitoring Agent"
        _svc_description_ = (
            "Collects hardware, software, and network metrics and reports them "
            "to the SIIMS central server."
        )

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            # Create a manual-reset event that SvcStop will set
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self._running = False
            self._worker_thread: threading.Thread | None = None

        def SvcStop(self):
            """Called by the Service Control Manager to stop the service."""
            logger.info("Service stop requested")
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            self._running = False
            win32event.SetEvent(self.hWaitStop)

        def SvcDoRun(self):
            """Service main entry point. Blocks until stop is signalled."""
            try:
                config, api_client, local_queue, heartbeat_collector = _build_components()
            except Exception as e:
                logger.critical("Failed to initialise agent: %s", e)
                self.ReportServiceStatus(win32service.SERVICE_STOPPED)
                return

            self._running = True
            self._worker_thread = threading.Thread(
                target=self._run_loop,
                args=(config, heartbeat_collector),
                daemon=True,
                name="siims-heartbeat",
            )
            self._worker_thread.start()
            logger.info("SIIMS Agent service started")

            # Main service thread: wait for the stop event using a secondary loop
            # WaitForSingleObject with 1-second timeout lets us check _running regularly
            while self._running:
                result = win32event.WaitForSingleObject(self.hWaitStop, 1000)
                if result == win32event.WAIT_OBJECT_0:
                    # Stop event was set
                    break

            # Graceful shutdown
            logger.info("Waiting for worker thread to finish...")
            if self._worker_thread is not None:
                self._worker_thread.join(timeout=10)
            logger.info("SIIMS Agent service stopped")

        def _run_loop(self, config, heartbeat_collector: HeartbeatCollector):
            """
            Background thread: repeatedly call heartbeat + software scan,
            then sleep for the configured interval.
            """
            import time
            logger.info("Heartbeat loop started (interval=%ds)", config.heartbeat_interval_seconds)
            while self._running:
                try:
                    heartbeat_collector.run_once()
                except Exception as e:
                    logger.error("Unhandled error in heartbeat loop: %s", e)

                # Sleep in short increments so we can respond to stop signal promptly
                remaining = config.heartbeat_interval_seconds
                while remaining > 0 and self._running:
                    sleep_chunk = min(remaining, 5)
                    import time as _time
                    _time.sleep(sleep_chunk)
                    remaining -= sleep_chunk

            logger.info("Heartbeat loop exited")

else:
    # Stub class for non-Windows platforms (import safety for tests)
    class SIIMSAgentService:  # type: ignore[no-redef]
        """Stub service class for non-Windows environments."""
        _svc_name_ = "SIIMSAgent"
        _svc_display_name_ = "SIIMS Monitoring Agent"

        def __init__(self, *args, **kwargs):
            raise NotImplementedError("Windows service is only available on Windows with pywin32 installed")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not _WIN32_AVAILABLE:
        print("ERROR: pywin32 is required to run the Windows service.")
        print("Install with: pip install pywin32")
        sys.exit(1)

    win32serviceutil.HandleCommandLine(SIIMSAgentService)
