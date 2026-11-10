"""
Unit tests for heartbeat.py.
Mocks APIClient and LocalQueue to test orchestration logic.
"""
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

# Import heartbeat at module level (conftest ensures monitoring-agent is on sys.path)
import heartbeat


class TestHeartbeatCollector(unittest.TestCase):
    """Tests for HeartbeatCollector.collect_and_send()."""

    def _make_config(self, heartbeat_interval=60, software_scan_interval_hours=6):
        config = MagicMock()
        config.computer_id = 42
        config.server_url = "http://localhost:8000"
        config.heartbeat_interval_seconds = heartbeat_interval
        config.software_scan_interval_hours = software_scan_interval_hours
        return config

    def _make_api_client(self, send_returns=True):
        client = MagicMock()
        client.send.return_value = send_returns
        return client

    def _make_local_queue(self, replay_returns=0):
        queue = MagicMock()
        queue.enqueue = MagicMock()
        queue.replay.return_value = replay_returns
        return queue

    @patch("heartbeat.collect_network_status", return_value={"is_online": True, "latency_ms": 5.0})
    @patch("heartbeat.collect_hardware_metrics", return_value={"cpu_percent": 30.0, "ram_percent": 50.0})
    def test_sends_heartbeat_on_success(self, mock_hw, mock_net):
        """When send() returns True, the heartbeat endpoint is called with correct payload."""
        config = self._make_config()
        api_client = self._make_api_client(send_returns=True)
        local_queue = self._make_local_queue()

        collector = heartbeat.HeartbeatCollector(config, api_client, local_queue)
        result = collector.collect_and_send()

        self.assertTrue(result)
        api_client.send.assert_called_once()
        call_args = api_client.send.call_args
        self.assertEqual(call_args[0][0], "/api/v1/agents/heartbeat")
        payload = call_args[0][1]
        self.assertEqual(payload["computer_id"], 42)
        self.assertIn("hardware", payload)
        self.assertIn("network", payload)
        self.assertIn("timestamp_utc", payload)

    @patch("heartbeat.collect_network_status", return_value={"is_online": False})
    @patch("heartbeat.collect_hardware_metrics", return_value={"cpu_percent": 90.0})
    def test_failed_send_returns_false(self, mock_hw, mock_net):
        """When send() returns False, collect_and_send returns False without raising."""
        config = self._make_config()
        api_client = self._make_api_client(send_returns=False)
        local_queue = self._make_local_queue()

        collector = heartbeat.HeartbeatCollector(config, api_client, local_queue)
        result = collector.collect_and_send()

        self.assertFalse(result)

    @patch("heartbeat.collect_network_status", return_value={"is_online": True})
    @patch("heartbeat.collect_hardware_metrics", return_value={"cpu_percent": 50.0})
    def test_replay_called_after_send(self, mock_hw, mock_net):
        """replay() is always called after the send attempt."""
        config = self._make_config()
        api_client = self._make_api_client(send_returns=True)
        local_queue = self._make_local_queue(replay_returns=2)

        collector = heartbeat.HeartbeatCollector(config, api_client, local_queue)
        collector.collect_and_send()

        local_queue.replay.assert_called_once_with(api_client)

    @patch("heartbeat.collect_network_status", return_value={"is_online": True})
    @patch("heartbeat.collect_hardware_metrics", return_value={"cpu_percent": 50.0})
    def test_replay_called_even_when_send_fails(self, mock_hw, mock_net):
        """replay() is called even when the main send fails."""
        config = self._make_config()
        api_client = self._make_api_client(send_returns=False)
        local_queue = self._make_local_queue()

        collector = heartbeat.HeartbeatCollector(config, api_client, local_queue)
        collector.collect_and_send()

        local_queue.replay.assert_called_once_with(api_client)

    @patch("heartbeat.collect_network_status", return_value={"is_online": True})
    @patch("heartbeat.collect_hardware_metrics", return_value={"cpu_percent": 50.0})
    def test_payload_contains_required_fields(self, mock_hw, mock_net):
        """Heartbeat payload must have computer_id, timestamp_utc, hardware, network."""
        config = self._make_config()
        api_client = self._make_api_client()
        local_queue = self._make_local_queue()

        collector = heartbeat.HeartbeatCollector(config, api_client, local_queue)
        collector.collect_and_send()

        payload = api_client.send.call_args[0][1]
        self.assertIn("computer_id", payload)
        self.assertIn("timestamp_utc", payload)
        self.assertIn("hardware", payload)
        self.assertIn("network", payload)

    @patch("heartbeat.collect_network_status", return_value={"is_online": True})
    @patch("heartbeat.collect_hardware_metrics", return_value={"cpu_percent": 50.0})
    def test_replay_error_does_not_propagate(self, mock_hw, mock_net):
        """An exception from replay() must not propagate out of collect_and_send."""
        config = self._make_config()
        api_client = self._make_api_client(send_returns=True)
        local_queue = self._make_local_queue()
        local_queue.replay.side_effect = RuntimeError("DB locked")

        collector = heartbeat.HeartbeatCollector(config, api_client, local_queue)
        # Should not raise
        result = collector.collect_and_send()
        self.assertTrue(result)


class TestSoftwareScan(unittest.TestCase):
    """Tests for HeartbeatCollector.software_scan()."""

    def _make_config(self, software_scan_interval_hours=6):
        config = MagicMock()
        config.computer_id = 1
        config.server_url = "http://localhost:8000"
        config.heartbeat_interval_seconds = 60
        config.software_scan_interval_hours = software_scan_interval_hours
        return config

    @patch("heartbeat.collect_software", return_value=[
        {"name": "App A", "publisher": "ACME", "version": "1.0", "install_date": None}
    ])
    def test_software_scan_sends_to_correct_endpoint(self, mock_sw):
        """software_scan() sends to /api/v1/agents/software-inventory."""
        config = self._make_config(software_scan_interval_hours=0)
        api_client = MagicMock()
        api_client.send.return_value = True
        local_queue = MagicMock()

        collector = heartbeat.HeartbeatCollector(config, api_client, local_queue)
        collector._last_software_scan = 0.0
        result = collector.software_scan()

        self.assertTrue(result)
        api_client.send.assert_called_once()
        endpoint = api_client.send.call_args[0][0]
        self.assertEqual(endpoint, "/api/v1/agents/software-inventory")

    @patch("heartbeat.collect_software", return_value=[])
    def test_software_scan_skipped_before_interval(self, mock_sw):
        """software_scan() should not send when the interval has not elapsed."""
        config = self._make_config(software_scan_interval_hours=6)
        api_client = MagicMock()
        local_queue = MagicMock()

        collector = heartbeat.HeartbeatCollector(config, api_client, local_queue)
        # Set last scan to "just now" so the 6-hour interval has not elapsed
        collector._last_software_scan = time.monotonic()
        result = collector.software_scan()

        api_client.send.assert_not_called()
        self.assertFalse(result)

    @patch("heartbeat.collect_software", return_value=[
        {"name": "App X", "publisher": "Pub", "version": "2.0", "install_date": "2024-01-01"}
    ])
    def test_software_payload_contains_software_list(self, mock_sw):
        """Software scan payload must contain the software list and computer_id."""
        config = self._make_config(software_scan_interval_hours=0)
        api_client = MagicMock()
        api_client.send.return_value = True
        local_queue = MagicMock()

        collector = heartbeat.HeartbeatCollector(config, api_client, local_queue)
        collector._last_software_scan = 0.0
        collector.software_scan()

        payload = api_client.send.call_args[0][1]
        self.assertIn("software", payload)
        self.assertIn("computer_id", payload)
        self.assertIn("timestamp_utc", payload)
        self.assertEqual(len(payload["software"]), 1)


class TestLocalQueueIntegration(unittest.TestCase):
    """Integration-style tests for LocalQueue with an in-memory SQLite database."""

    def test_enqueue_and_replay_success(self):
        """Enqueue a payload, then replay it successfully."""
        import local_queue as lq
        queue = lq.LocalQueue(db_path=":memory:")

        api_client = MagicMock()
        api_client.base_url = "http://localhost:8000"
        mock_response = MagicMock()
        mock_response.status_code = 200
        api_client._session.post.return_value = mock_response

        queue.enqueue("/api/v1/agents/heartbeat", {"computer_id": 1, "data": "test"})
        self.assertEqual(queue.queue_size(), 1)

        replayed = queue.replay(api_client)
        self.assertEqual(replayed, 1)
        self.assertEqual(queue.queue_size(), 0)

    def test_failed_replay_increments_attempts(self):
        """When replay send fails, the attempts counter increments."""
        import local_queue as lq
        queue = lq.LocalQueue(db_path=":memory:")

        api_client = MagicMock()
        api_client.base_url = "http://localhost:8000"
        mock_response = MagicMock()
        mock_response.status_code = 500
        api_client._session.post.return_value = mock_response

        queue.enqueue("/api/v1/agents/heartbeat", {"computer_id": 1})
        queue.replay(api_client)

        self.assertEqual(queue.queue_size(), 1)
        with queue._connect() as conn:
            row = conn.execute("SELECT attempts FROM queued_payloads").fetchone()
            self.assertEqual(row["attempts"], 1)

    def test_prune_removes_old_entries(self):
        """Entries older than max_queue_age_days must be pruned."""
        import local_queue as lq
        queue = lq.LocalQueue(db_path=":memory:", max_queue_age_days=7)

        with queue._connect() as conn:
            conn.execute(
                "INSERT INTO queued_payloads (endpoint, payload_json, created_at) "
                "VALUES (?, ?, datetime('now', '-10 days'))",
                ("/api/v1/agents/heartbeat", '{"old": true}'),
            )
            conn.commit()

        self.assertEqual(queue.queue_size(), 1)
        pruned = queue.prune()
        self.assertEqual(pruned, 1)
        self.assertEqual(queue.queue_size(), 0)

    def test_prune_removes_exhausted_entries(self):
        """Entries with 10+ failed attempts must be pruned."""
        import local_queue as lq
        queue = lq.LocalQueue(db_path=":memory:")

        with queue._connect() as conn:
            conn.execute(
                "INSERT INTO queued_payloads (endpoint, payload_json, attempts) "
                "VALUES (?, ?, 10)",
                ("/api/v1/agents/heartbeat", '{"exhausted": true}'),
            )
            conn.commit()

        self.assertEqual(queue.queue_size(), 1)
        pruned = queue.prune()
        self.assertEqual(pruned, 1)
        self.assertEqual(queue.queue_size(), 0)

    def test_fifo_order(self):
        """replay() must process entries in insertion order (FIFO)."""
        import local_queue as lq
        queue = lq.LocalQueue(db_path=":memory:")

        processed_urls = []

        api_client = MagicMock()
        api_client.base_url = "http://localhost:8000"

        def post_side_effect(url, json=None, timeout=None):
            processed_urls.append(url)
            resp = MagicMock()
            resp.status_code = 200
            return resp

        api_client._session.post.side_effect = post_side_effect

        queue.enqueue("/first", {"order": 1})
        queue.enqueue("/second", {"order": 2})
        queue.enqueue("/third", {"order": 3})

        queue.replay(api_client)

        self.assertEqual(len(processed_urls), 3)
        self.assertTrue(processed_urls[0].endswith("/first"))
        self.assertTrue(processed_urls[1].endswith("/second"))
        self.assertTrue(processed_urls[2].endswith("/third"))

    def test_queue_size_empty(self):
        """queue_size() returns 0 on a fresh queue."""
        import local_queue as lq
        queue = lq.LocalQueue(db_path=":memory:")
        self.assertEqual(queue.queue_size(), 0)

    def test_multiple_enqueue(self):
        """Enqueuing multiple items increments the queue size."""
        import local_queue as lq
        queue = lq.LocalQueue(db_path=":memory:")
        queue.enqueue("/ep1", {"a": 1})
        queue.enqueue("/ep2", {"b": 2})
        queue.enqueue("/ep3", {"c": 3})
        self.assertEqual(queue.queue_size(), 3)


if __name__ == "__main__":
    unittest.main()
