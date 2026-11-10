"""
API client for SIIMS Monitoring Agent.
Sends monitoring data to the backend with exponential backoff retry logic.
Delegates to LocalQueue on persistent failure.
"""
import logging
import time
from typing import TYPE_CHECKING, Any

import requests
from requests.adapters import HTTPAdapter

if TYPE_CHECKING:
    from config import Config
    from local_queue import LocalQueue

logger = logging.getLogger(__name__)

# Retry delay schedule (seconds): attempt 1 immediately, then these waits before each retry
_RETRY_DELAYS = [5, 15, 30]  # waits before attempts 2, 3, 4


class APIClient:
    """
    HTTP client for communicating with the SIIMS backend.
    
    Implements exponential backoff: up to 4 attempts total.
    On all 4 failures, delegates the payload to LocalQueue for later replay.
    """

    def __init__(self, config: "Config", local_queue: "LocalQueue | None" = None):
        self._config = config
        self._local_queue = local_queue
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SIIMS-Agent/1.0",
        })
        # Mount a simple adapter (no built-in retries — we do retries manually)
        adapter = HTTPAdapter(max_retries=0)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    @property
    def base_url(self) -> str:
        return self._config.server_url

    def set_queue(self, local_queue: "LocalQueue") -> None:
        """Set the local queue reference (allows deferred injection)."""
        self._local_queue = local_queue

    def send(self, endpoint: str, payload: dict[str, Any]) -> bool:
        """
        POST a JSON payload to the given endpoint with exponential backoff.
        
        Attempts:
            1. Immediately
            2. After 5 seconds
            3. After 15 seconds
            4. After 30 seconds
        
        On all failures, enqueues the payload for later replay.
        
        Args:
            endpoint: API path, e.g. '/api/v1/agents/heartbeat'
            payload: JSON-serialisable dict
        
        Returns:
            True on success, False if all attempts failed.
        """
        url = self.base_url + endpoint
        max_attempts = self._config.retry_attempts + 1  # e.g. 3 retries = 4 total attempts
        # Cap retry delays to the number of additional attempts we can make
        delays = _RETRY_DELAYS[: max_attempts - 1]

        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = self._session.post(url, json=payload, timeout=15)
                if response.status_code in (200, 201, 202, 204):
                    logger.debug("Sent to %s (attempt %d/%d): %s", endpoint, attempt, max_attempts, response.status_code)
                    return True
                else:
                    logger.warning(
                        "HTTP %d from %s (attempt %d/%d)",
                        response.status_code, endpoint, attempt, max_attempts
                    )
                    last_error = f"HTTP {response.status_code}"
            except requests.exceptions.Timeout:
                logger.warning("Timeout contacting %s (attempt %d/%d)", url, attempt, max_attempts)
                last_error = "Timeout"
            except requests.exceptions.ConnectionError as e:
                logger.warning("Connection error to %s (attempt %d/%d): %s", url, attempt, max_attempts, e)
                last_error = str(e)
            except Exception as e:
                logger.error("Unexpected error sending to %s (attempt %d/%d): %s", url, attempt, max_attempts, e)
                last_error = str(e)

            # Wait before the next attempt (if there is one)
            if attempt <= len(delays):
                wait = delays[attempt - 1]
                logger.debug("Waiting %ds before retry %d", wait, attempt + 1)
                time.sleep(wait)

        # All attempts failed
        logger.error("All %d send attempts to %s failed. Last error: %s", max_attempts, endpoint, last_error)

        if self._local_queue is not None:
            try:
                self._local_queue.enqueue(endpoint, payload)
                logger.info("Payload queued for later replay: %s", endpoint)
            except Exception as e:
                logger.error("Failed to enqueue payload: %s", e)

        return False

    def get_config(self) -> dict[str, Any]:
        """
        Fetch agent configuration from the backend.
        
        Returns:
            Parsed JSON response dict, or {} on any error.
        """
        url = self.base_url + "/api/v1/agents/config"
        try:
            response = self._session.get(url, timeout=15)
            if response.status_code == 200:
                return response.json()
            logger.warning("get_config returned HTTP %d", response.status_code)
        except Exception as e:
            logger.warning("get_config failed: %s", e)
        return {}

    def register_self(self) -> bool:
        """
        Register this agent with the backend (not used in v1 — computer_id is pre-configured).
        Reserved for future use.
        
        Returns:
            False (not implemented in v1)
        """
        logger.debug("register_self() is not used in v1; computer_id is pre-configured in config.ini")
        return False
