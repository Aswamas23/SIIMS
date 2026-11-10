"""
Unit tests for network.py.
Mocks subprocess.run() and psutil to avoid real network calls.
"""
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

# Import network at module level (conftest ensures monitoring-agent is on sys.path)
import network


class TestParsePingOutputWindows(unittest.TestCase):
    """Tests for parse_ping_output() with Windows-format output."""

    def test_parses_average_latency(self):
        stdout = (
            "Pinging 192.168.1.1 with 32 bytes of data:\n"
            "Reply from 192.168.1.1: bytes=32 time=12ms TTL=64\n"
            "\n"
            "Ping statistics for 192.168.1.1:\n"
            "    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),\n"
            "Approximate round trip times in milli-seconds:\n"
            "    Minimum = 11ms, Maximum = 13ms, Average = 12ms\n"
        )
        result = network.parse_ping_output(stdout, platform="win32")
        self.assertEqual(result["latency_ms"], 12.0)
        self.assertEqual(result["packet_loss_percent"], 0.0)

    def test_parses_50_percent_loss(self):
        stdout = (
            "Ping statistics for 10.0.0.1:\n"
            "    Packets: Sent = 4, Received = 2, Lost = 2 (50% loss),\n"
            "Approximate round trip times in milli-seconds:\n"
            "    Minimum = 20ms, Maximum = 25ms, Average = 22ms\n"
        )
        result = network.parse_ping_output(stdout, platform="win32")
        self.assertEqual(result["packet_loss_percent"], 50.0)
        self.assertEqual(result["latency_ms"], 22.0)

    def test_empty_stdout_returns_none_values(self):
        result = network.parse_ping_output("", platform="win32")
        self.assertIsNone(result["latency_ms"])
        self.assertIsNone(result["packet_loss_percent"])

    def test_100_percent_loss_no_average_line(self):
        stdout = (
            "Ping statistics for 10.0.0.99:\n"
            "    Packets: Sent = 4, Received = 0, Lost = 4 (100% loss),\n"
        )
        result = network.parse_ping_output(stdout, platform="win32")
        self.assertEqual(result["packet_loss_percent"], 100.0)
        # No Average line → latency is None
        self.assertIsNone(result["latency_ms"])

    def test_zero_loss_zero_latency_format(self):
        stdout = (
            "Ping statistics for 127.0.0.1:\n"
            "    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),\n"
            "Approximate round trip times in milli-seconds:\n"
            "    Minimum = 0ms, Maximum = 1ms, Average = 0ms\n"
        )
        result = network.parse_ping_output(stdout, platform="win32")
        self.assertEqual(result["latency_ms"], 0.0)
        self.assertEqual(result["packet_loss_percent"], 0.0)


class TestParsePingOutputLinux(unittest.TestCase):
    """Tests for parse_ping_output() with Linux-format output."""

    def test_parses_rtt_avg(self):
        stdout = (
            "PING 192.168.1.1 (192.168.1.1) 56(84) bytes of data.\n"
            "64 bytes from 192.168.1.1: icmp_seq=1 ttl=64 time=0.456 ms\n"
            "\n"
            "--- 192.168.1.1 ping statistics ---\n"
            "4 packets transmitted, 4 received, 0% packet loss, time 3005ms\n"
            "rtt min/avg/max/mdev = 0.400/0.456/0.520/0.040 ms\n"
        )
        result = network.parse_ping_output(stdout, platform="linux")
        self.assertAlmostEqual(result["latency_ms"], 0.456, places=2)
        self.assertEqual(result["packet_loss_percent"], 0.0)

    def test_parses_50_percent_packet_loss_linux(self):
        stdout = (
            "--- 10.0.0.1 ping statistics ---\n"
            "4 packets transmitted, 2 received, 50% packet loss, time 3000ms\n"
            "rtt min/avg/max/mdev = 10.0/15.5/21.0/4.5 ms\n"
        )
        result = network.parse_ping_output(stdout, platform="linux")
        self.assertEqual(result["packet_loss_percent"], 50.0)
        self.assertAlmostEqual(result["latency_ms"], 15.5, places=1)

    def test_none_values_on_no_match(self):
        result = network.parse_ping_output("garbage output", platform="linux")
        self.assertIsNone(result["latency_ms"])
        self.assertIsNone(result["packet_loss_percent"])


class TestPingHost(unittest.TestCase):
    """Tests for ping_host()."""

    @patch("network.subprocess.run")
    def test_successful_ping_windows(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                "Ping statistics for 192.168.1.1:\n"
                "    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),\n"
                "Approximate round trip times in milli-seconds:\n"
                "    Minimum = 10ms, Maximum = 15ms, Average = 12ms\n"
            ),
            stderr="",
        )
        with patch.object(network.sys, "platform", "win32"):
            result = network.ping_host("192.168.1.1", count=4)

        self.assertTrue(result["is_online"])
        self.assertEqual(result["latency_ms"], 12.0)
        self.assertEqual(result["packet_loss_percent"], 0.0)

    @patch("network.subprocess.run")
    def test_failed_ping_returns_offline(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=(
                "Ping statistics for 10.0.0.99:\n"
                "    Packets: Sent = 4, Received = 0, Lost = 4 (100% loss),\n"
            ),
            stderr="",
        )
        result = network.ping_host("10.0.0.99")
        self.assertFalse(result["is_online"])

    @patch("network.subprocess.run", side_effect=Exception("subprocess error"))
    def test_exception_returns_offline(self, mock_run):
        result = network.ping_host("bad-host")
        self.assertFalse(result["is_online"])
        self.assertIsNone(result["latency_ms"])

    @patch("network.subprocess.run", side_effect=subprocess.TimeoutExpired("ping", 30))
    def test_timeout_returns_offline(self, mock_run):
        result = network.ping_host("slow-host")
        self.assertFalse(result["is_online"])

    def test_empty_hostname_returns_offline(self):
        result = network.ping_host("")
        self.assertFalse(result["is_online"])

    @patch("network.subprocess.run")
    def test_returncode_0_means_online(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Minimum = 5ms, Maximum = 8ms, Average = 6ms\n(0% loss)",
            stderr="",
        )
        result = network.ping_host("good-host")
        self.assertTrue(result["is_online"])


class TestGetInterfaces(unittest.TestCase):
    """Tests for get_interfaces()."""

    @patch("network.psutil.net_if_addrs")
    @patch("network.psutil.net_if_stats")
    def test_returns_interface_list(self, mock_stats, mock_addrs):
        import socket
        stat_mock = MagicMock(isup=True, speed=1000)
        mock_stats.return_value = {"Ethernet": stat_mock}

        addr_mock = MagicMock(family=socket.AF_INET, address="192.168.1.100")
        mock_addrs.return_value = {"Ethernet": [addr_mock]}

        result = network.get_interfaces()

        self.assertEqual(len(result), 1)
        iface = result[0]
        self.assertEqual(iface["name"], "Ethernet")
        self.assertTrue(iface["is_up"])
        self.assertEqual(iface["speed_mbps"], 1000)
        self.assertIn("192.168.1.100", iface["ip_addresses"])

    @patch("network.psutil.net_if_stats")
    @patch("network.psutil.net_if_addrs", return_value={})
    def test_down_interface(self, mock_addrs, mock_stats):
        stat_mock = MagicMock(isup=False, speed=0)
        mock_stats.return_value = {"Wi-Fi": stat_mock}

        result = network.get_interfaces()
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["is_up"])
        self.assertIsNone(result[0]["speed_mbps"])  # speed=0 → None

    @patch("network.psutil.net_if_stats", side_effect=Exception("psutil error"))
    def test_exception_returns_empty_list(self, mock_stats):
        result = network.get_interfaces()
        self.assertEqual(result, [])


class TestExtractHostname(unittest.TestCase):
    """Tests for _extract_hostname()."""

    def test_extracts_from_full_url_with_port(self):
        self.assertEqual(network._extract_hostname("http://192.168.1.50:8000"), "192.168.1.50")

    def test_extracts_from_https_url(self):
        self.assertEqual(network._extract_hostname("https://server.school.local/api"), "server.school.local")

    def test_bare_hostname(self):
        self.assertEqual(network._extract_hostname("server.school.local"), "server.school.local")

    def test_bare_ip(self):
        self.assertEqual(network._extract_hostname("192.168.1.1"), "192.168.1.1")

    def test_url_no_path(self):
        self.assertEqual(network._extract_hostname("http://10.0.0.1"), "10.0.0.1")


class TestCollectNetworkStatus(unittest.TestCase):
    """Tests for collect_network_status()."""

    @patch("network.get_interfaces", return_value=[])
    @patch("network.ping_host")
    def test_calls_ping_with_server_hostname(self, mock_ping, mock_ifaces):
        mock_ping.return_value = {
            "is_online": True, "latency_ms": 5.0, "packet_loss_percent": 0.0
        }
        result = network.collect_network_status("http://192.168.1.50:8000")

        mock_ping.assert_called_once_with("192.168.1.50")
        self.assertTrue(result["is_online"])
        self.assertEqual(result["latency_ms"], 5.0)

    @patch("network.get_interfaces", return_value=[
        {"name": "eth0", "is_up": True, "speed_mbps": 100, "ip_addresses": []}
    ])
    @patch("network.ping_host", return_value={
        "is_online": False, "latency_ms": None, "packet_loss_percent": None
    })
    def test_includes_interfaces_in_result(self, mock_ping, mock_ifaces):
        result = network.collect_network_status("http://server:8000")
        self.assertEqual(len(result["interfaces"]), 1)
        self.assertEqual(result["interfaces"][0]["name"], "eth0")

    @patch("network.get_interfaces", return_value=[])
    @patch("network.ping_host", return_value={
        "is_online": False, "latency_ms": None, "packet_loss_percent": None
    })
    def test_offline_server_sets_is_online_false(self, mock_ping, mock_ifaces):
        result = network.collect_network_status("http://unreachable:8000")
        self.assertFalse(result["is_online"])

    @patch("network.get_interfaces", return_value=[])
    def test_no_server_url_skips_ping(self, mock_ifaces):
        result = network.collect_network_status("")
        # No ping called, is_online defaults to False
        self.assertFalse(result["is_online"])
        self.assertIsNone(result["server_hostname"])


if __name__ == "__main__":
    unittest.main()
