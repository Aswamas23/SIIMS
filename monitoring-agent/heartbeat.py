"""
Heartbeat collector for SIIMS Monitoring Agent.
Orchestrates hardware/network collection, payload assembly, and transmission.
"""
import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from hardware import collect_hardware_metrics
from network import collect_network_status
from software import collect_software

if TYPE_CHECKING:
    from api_client import APIClient
    from config import Config
    from local_queue import LocalQueue

logger = logging.getLogger(__name__)


class HeartbeatCollector:
    """
    Collects hardware and network metrics and sends them to the SIIMS backend.
    Also manages periodic software inventory scans.
    """

    def __init__(self, config: "Config", api_client: "APIClient", local_queue: "LocalQueue"):
        self._config = config
        self._api_client = api_client
        self._local_queue = local_queue
        self._last_software_scan: float = 0.0  # Unix timestamp of last scan

    def collect_and_send(self) -> bool:
        """
        Collect hardware and network metrics, assemble the payload, and send it.
        
        On API failure, the payload is enqueued in the LocalQueue.
        After attempting to send, any queued payloads are replayed.
        
        Returns:
            True if the heartbeat was sent successfully, False otherwise.
        """
        logger.debug("Starting heartbeat collection")

        # Collect metrics
        hardware = collect_hardware_metrics()
        network = collect_network_status(server_url=self._config.server_url)

        # Assemble payload
        payload = {
            "computer_id": self._config.computer_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "hardware": hardware,
            "network": network,
        }

        # Attempt to send; api_client.send() handles retries and enqueuing on failure
        endpoint = "/api/v1/agents/heartbeat"
        success = self._api_client.send(endpoint, payload)

        if success:
            logger.debug("Heartbeat sent successfully")
        else:
            logger.warning("Heartbeat send failed; payload queued for replay")

        # Replay any buffered payloads now that we may have connectivity
        try:
            replayed = self._local_queue.replay(self._api_client)
            if replayed > 0:
                logger.info("Replayed %d buffered payload(s)", replayed)
        except Exception as e:
            logger.warning("Queue replay error: %s", e)

        return success

    def software_scan(self) -> bool:
        """
        Collect software inventory and send it to the backend.
        Only runs if the configured interval has elapsed since the last scan.
        
        Returns:
            True if scan was performed and sent successfully.
            False if the interval has not elapsed or if the send failed.
            None if the scan was skipped (interval not elapsed).
        """
        interval_seconds = self._config.software_scan_interval_hours * 3600
        now = time.monotonic()
        elapsed = now - self._last_software_scan

        if elapsed < interval_seconds:
            remaining = interval_seconds - elapsed
            logger.debug(
                "Software scan skipped (next scan in %.0f seconds)", remaining
            )
            return False

        logger.info("Starting software inventory scan")
        try:
            software_list = collect_software()
        except Exception as e:
            logger.error("Software collection failed: %s", e)
            return False

        payload = {
            "computer_id": self._config.computer_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "software": software_list,
        }

        endpoint = "/api/v1/agents/software-inventory"
        success = self._api_client.send(endpoint, payload)

        if success:
            self._last_software_scan = now
            logger.info("Software inventory sent: %d items", len(software_list))
        else:
            logger.warning("Software inventory send failed; payload queued")
            # Still update the timestamp to avoid hammering the queue with large payloads
            self._last_software_scan = now

        return success

    def run_once(self) -> None:
        """
        Execute one full heartbeat + optional software scan cycle.
        Intended to be called from the agent's main loop.
        """
        self.collect_and_send()
        self.software_scan()
