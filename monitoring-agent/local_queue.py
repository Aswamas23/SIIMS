"""
Local SQLite queue for SIIMS Monitoring Agent.
Buffers payloads when the server is unreachable and replays them on reconnection.
Uses stdlib sqlite3 only — no SQLAlchemy dependency.
"""
import json
import logging
import sqlite3
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from api_client import APIClient

logger = logging.getLogger(__name__)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS queued_payloads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint    TEXT    NOT NULL,
    payload_json TEXT   NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    attempts    INTEGER NOT NULL DEFAULT 0
);
"""

_CREATE_INDEX_SQL = "CREATE INDEX IF NOT EXISTS ix_queued_payloads_created_at ON queued_payloads (created_at);"


class LocalQueue:
    """
    SQLite-backed FIFO queue for buffering monitoring payloads.
    
    Payloads are replayed in insertion order when the server becomes available.
    Stale entries (older than max_queue_age_days) and exhausted entries
    (>= 10 failed attempts) are pruned on every replay cycle.
    
    For ':memory:' databases a single persistent connection is kept so that
    all operations share the same in-memory database (each sqlite3.connect()
    to ':memory:' would otherwise create a fresh, empty database).
    """

    def __init__(self, db_path: str, max_queue_age_days: int = 7):
        """
        Args:
            db_path: Path to the SQLite database file. Use ':memory:' for tests.
            max_queue_age_days: Maximum age of queued entries before pruning.
        """
        self._db_path = db_path
        self._max_queue_age_days = max_queue_age_days
        # For in-memory databases, hold one persistent connection.
        self._persistent_conn: sqlite3.Connection | None = None
        if db_path == ":memory:":
            self._persistent_conn = self._make_connection()
        self._init_db()

    def _make_connection(self) -> sqlite3.Connection:
        """Open a raw SQLite connection and configure it."""
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # WAL mode only makes sense for file-based databases
        if self._db_path != ":memory:":
            conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _connect(self) -> sqlite3.Connection:
        """
        Return a SQLite connection.
        
        For ':memory:' databases, returns the persistent connection so all
        operations share the same in-memory database.
        For file-based databases, opens a new connection per call.
        """
        if self._persistent_conn is not None:
            return self._persistent_conn
        return self._make_connection()

    def _init_db(self) -> None:
        """Create the queue table and index if they do not exist."""
        try:
            with self._connect() as conn:
                conn.execute(_CREATE_TABLE_SQL)
                conn.execute(_CREATE_INDEX_SQL)
                conn.commit()
        except Exception as e:
            logger.error("Failed to initialise local queue database: %s", e)
            raise

    def enqueue(self, endpoint: str, payload: dict[str, Any]) -> None:
        """
        Add a payload to the queue for later transmission.
        
        Args:
            endpoint: API endpoint path (e.g. '/api/v1/agents/heartbeat')
            payload: JSON-serialisable dict
        """
        try:
            payload_json = json.dumps(payload)
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO queued_payloads (endpoint, payload_json) VALUES (?, ?)",
                    (endpoint, payload_json),
                )
                conn.commit()
            logger.debug("Enqueued payload for %s", endpoint)
        except Exception as e:
            logger.error("Failed to enqueue payload for %s: %s", endpoint, e)

    def replay(self, api_client: "APIClient") -> int:
        """
        Attempt to send queued payloads to the server.
        Processes up to 50 entries per call in FIFO order.
        Prunes stale/exhausted entries before replaying.
        
        Args:
            api_client: Configured APIClient instance (used for direct HTTP call,
                        not via api_client.send() to avoid re-queuing on failure)
        
        Returns:
            Number of successfully replayed entries
        """
        self.prune()

        sent_count = 0
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT id, endpoint, payload_json, attempts "
                    "FROM queued_payloads "
                    "ORDER BY id ASC "
                    "LIMIT 50"
                ).fetchall()
        except Exception as e:
            logger.error("Failed to read from local queue: %s", e)
            return 0

        for row in rows:
            row_id = row["id"]
            endpoint = row["endpoint"]
            attempts = row["attempts"]

            try:
                payload = json.loads(row["payload_json"])
            except json.JSONDecodeError as e:
                logger.warning("Invalid JSON in queue entry %d, discarding: %s", row_id, e)
                self._delete_entry(row_id)
                continue

            # Attempt a single direct send (bypasses the retry/queue-again loop)
            success = self._direct_send(api_client, endpoint, payload)

            if success:
                self._delete_entry(row_id)
                sent_count += 1
                logger.debug("Replayed queued payload %d to %s", row_id, endpoint)
            else:
                self._increment_attempts(row_id, attempts + 1)

        if sent_count > 0:
            logger.info("Replayed %d queued payload(s)", sent_count)

        return sent_count

    def prune(self) -> int:
        """
        Remove entries that are too old or have too many failed attempts.
        
        Removes entries where:
        - created_at < now - max_queue_age_days
        - attempts >= 10
        
        Returns:
            Number of entries pruned
        """
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    "DELETE FROM queued_payloads "
                    "WHERE created_at < datetime('now', ?) OR attempts >= 10",
                    (f"-{self._max_queue_age_days} days",),
                )
                conn.commit()
                pruned = cursor.rowcount
                if pruned > 0:
                    logger.info("Pruned %d stale/exhausted queue entries", pruned)
                return pruned
        except Exception as e:
            logger.error("Failed to prune local queue: %s", e)
            return 0

    def _delete_entry(self, row_id: int) -> None:
        """Delete a successfully replayed entry from the queue."""
        try:
            with self._connect() as conn:
                conn.execute("DELETE FROM queued_payloads WHERE id = ?", (row_id,))
                conn.commit()
        except Exception as e:
            logger.warning("Failed to delete queue entry %d: %s", row_id, e)

    def _increment_attempts(self, row_id: int, new_attempts: int) -> None:
        """Increment the attempt counter for a failed entry."""
        try:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE queued_payloads SET attempts = ? WHERE id = ?",
                    (new_attempts, row_id),
                )
                conn.commit()
        except Exception as e:
            logger.warning("Failed to update attempts for queue entry %d: %s", row_id, e)

    def _direct_send(self, api_client: "APIClient", endpoint: str, payload: dict) -> bool:
        """
        Send a single payload directly via the api_client's HTTP session,
        without triggering the retry/re-queue logic.
        
        Returns True on HTTP 2xx, False otherwise.
        """
        try:
            url = api_client.base_url + endpoint
            response = api_client._session.post(url, json=payload, timeout=15)
            return response.status_code in (200, 201, 202, 204)
        except Exception as e:
            logger.debug("Direct send failed for queue entry at %s: %s", endpoint, e)
            return False

    def queue_size(self) -> int:
        """Return the current number of entries in the queue."""
        try:
            with self._connect() as conn:
                row = conn.execute("SELECT COUNT(*) FROM queued_payloads").fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.warning("Failed to get queue size: %s", e)
            return 0
