"""
Unit tests for hardware.py.
All system calls are mocked — no real hardware access required.
"""
import unittest
from unittest.mock import MagicMock, patch

# Import hardware at module level (conftest ensures monitoring-agent is on sys.path)
import hardware


class TestCollectHardwareMetrics(unittest.TestCase):
    """Tests for the main collect_hardware_metrics() function."""

    def _make_virtual_memory(self, percent=55.0, used=4 * 1024**3, total=8 * 1024**3):
        mem = MagicMock()
        mem.percent = percent
        mem.used = used
        mem.total = total
        return mem

    def _make_disk_usage(self, percent=70.0, used=140 * 1024**3, total=200 * 1024**3, free=60 * 1024**3):
        disk = MagicMock()
        disk.percent = percent
        disk.used = used
        disk.total = total
        disk.free = free
        return disk

    @patch("hardware._get_battery_info", return_value=None)
    @patch("hardware._get_smart_status", return_value="unavailable")
    @patch("hardware._get_cpu_temperature", return_value=None)
    @patch("hardware.time.time", return_value=1000.0)
    @patch("hardware.psutil.boot_time", return_value=0.0)
    @patch("hardware.psutil.disk_usage")
    @patch("hardware.psutil.virtual_memory")
    @patch("hardware.psutil.cpu_percent", return_value=42.0)
    def test_returns_all_expected_keys(
        self, mock_cpu, mock_vmem, mock_disk, mock_boot,
        mock_time, mock_temp, mock_smart, mock_battery
    ):
        mock_vmem.return_value = self._make_virtual_memory()
        mock_disk.return_value = self._make_disk_usage()

        result = hardware.collect_hardware_metrics()

        expected_keys = {
            "cpu_percent", "ram_percent", "ram_used_gb", "ram_total_gb",
            "disk_percent", "disk_used_gb", "disk_total_gb", "disk_free_gb",
            "uptime_seconds", "cpu_temperature_celsius", "smart_status", "battery",
        }
        self.assertEqual(set(result.keys()), expected_keys)

    @patch("hardware._get_battery_info", return_value=None)
    @patch("hardware._get_smart_status", return_value="unavailable")
    @patch("hardware._get_cpu_temperature", return_value=None)
    @patch("hardware.time.time", return_value=1000.0)
    @patch("hardware.psutil.boot_time", return_value=0.0)
    @patch("hardware.psutil.disk_usage")
    @patch("hardware.psutil.virtual_memory")
    @patch("hardware.psutil.cpu_percent", return_value=42.0)
    def test_correct_cpu_value(
        self, mock_cpu, mock_vmem, mock_disk, mock_boot,
        mock_time, mock_temp, mock_smart, mock_battery
    ):
        mock_vmem.return_value = self._make_virtual_memory()
        mock_disk.return_value = self._make_disk_usage()

        result = hardware.collect_hardware_metrics()
        self.assertEqual(result["cpu_percent"], 42.0)

    @patch("hardware._get_battery_info", return_value=None)
    @patch("hardware._get_smart_status", return_value="unavailable")
    @patch("hardware._get_cpu_temperature", return_value=None)
    @patch("hardware.time.time", return_value=3600.0)
    @patch("hardware.psutil.boot_time", return_value=0.0)
    @patch("hardware.psutil.disk_usage")
    @patch("hardware.psutil.virtual_memory")
    @patch("hardware.psutil.cpu_percent", return_value=75.5)
    def test_correct_uptime(
        self, mock_cpu, mock_vmem, mock_disk, mock_boot,
        mock_time, mock_temp, mock_smart, mock_battery
    ):
        mock_vmem.return_value = self._make_virtual_memory()
        mock_disk.return_value = self._make_disk_usage()

        result = hardware.collect_hardware_metrics()
        # uptime = time.time() - boot_time() = 3600.0 - 0.0
        self.assertAlmostEqual(result["uptime_seconds"], 3600.0, places=0)

    @patch("hardware._get_battery_info", return_value=None)
    @patch("hardware._get_smart_status", return_value="unavailable")
    @patch("hardware._get_cpu_temperature", return_value=None)
    @patch("hardware.time.time", return_value=1000.0)
    @patch("hardware.psutil.boot_time", return_value=0.0)
    @patch("hardware.psutil.disk_usage")
    @patch("hardware.psutil.virtual_memory")
    @patch("hardware.psutil.cpu_percent", side_effect=Exception("Hardware read error"))
    def test_cpu_exception_returns_none_not_crash(
        self, mock_cpu, mock_vmem, mock_disk, mock_boot,
        mock_time, mock_temp, mock_smart, mock_battery
    ):
        """When cpu_percent raises, cpu_percent field must be None — not an exception."""
        mock_vmem.return_value = self._make_virtual_memory()
        mock_disk.return_value = self._make_disk_usage()

        result = hardware.collect_hardware_metrics()
        self.assertIsNone(result["cpu_percent"])
        # Other metrics should still be collected
        self.assertIsNotNone(result["ram_percent"])

    @patch("hardware._get_battery_info", return_value=None)
    @patch("hardware._get_smart_status", return_value="unavailable")
    @patch("hardware._get_cpu_temperature", return_value=None)
    @patch("hardware.time.time", return_value=1000.0)
    @patch("hardware.psutil.boot_time", return_value=0.0)
    @patch("hardware.psutil.disk_usage", side_effect=Exception("Disk error"))
    @patch("hardware.psutil.virtual_memory", side_effect=Exception("RAM error"))
    @patch("hardware.psutil.cpu_percent", side_effect=Exception("CPU error"))
    def test_all_metrics_fail_returns_none_values(
        self, mock_cpu, mock_vmem, mock_disk, mock_boot,
        mock_time, mock_temp, mock_smart, mock_battery
    ):
        """When all metrics fail, values are None — function never raises."""
        result = hardware.collect_hardware_metrics()
        self.assertIsNone(result["cpu_percent"])
        self.assertIsNone(result["ram_percent"])
        self.assertIsNone(result["disk_percent"])

    @patch("hardware._get_battery_info", return_value=None)
    @patch("hardware._get_smart_status", return_value="unavailable")
    @patch("hardware._get_cpu_temperature", return_value=None)
    @patch("hardware.time.time", return_value=1000.0)
    @patch("hardware.psutil.boot_time", return_value=0.0)
    @patch("hardware.psutil.disk_usage")
    @patch("hardware.psutil.virtual_memory")
    @patch("hardware.psutil.cpu_percent", return_value=50.0)
    def test_ram_metrics_calculated_correctly(
        self, mock_cpu, mock_vmem, mock_disk, mock_boot,
        mock_time, mock_temp, mock_smart, mock_battery
    ):
        mock_vmem.return_value = self._make_virtual_memory(
            percent=60.0,
            used=6 * 1024**3,
            total=10 * 1024**3,
        )
        mock_disk.return_value = self._make_disk_usage()

        result = hardware.collect_hardware_metrics()
        self.assertEqual(result["ram_percent"], 60.0)
        self.assertAlmostEqual(result["ram_used_gb"], 6.0, places=1)
        self.assertAlmostEqual(result["ram_total_gb"], 10.0, places=1)

    @patch("hardware._get_battery_info", return_value=None)
    @patch("hardware._get_smart_status", return_value="healthy")
    @patch("hardware._get_cpu_temperature", return_value=55.3)
    @patch("hardware.time.time", return_value=1000.0)
    @patch("hardware.psutil.boot_time", return_value=0.0)
    @patch("hardware.psutil.disk_usage")
    @patch("hardware.psutil.virtual_memory")
    @patch("hardware.psutil.cpu_percent", return_value=50.0)
    def test_temperature_and_smart_pass_through(
        self, mock_cpu, mock_vmem, mock_disk, mock_boot,
        mock_time, mock_temp, mock_smart, mock_battery
    ):
        mock_vmem.return_value = self._make_virtual_memory()
        mock_disk.return_value = self._make_disk_usage()

        result = hardware.collect_hardware_metrics()
        self.assertEqual(result["cpu_temperature_celsius"], 55.3)
        self.assertEqual(result["smart_status"], "healthy")


class TestGetCpuPercent(unittest.TestCase):
    """Tests for the _get_cpu_percent helper."""

    @patch("hardware.psutil.cpu_percent", return_value=88.5)
    def test_returns_float_value(self, mock_cpu):
        self.assertEqual(hardware._get_cpu_percent(), 88.5)

    @patch("hardware.psutil.cpu_percent", side_effect=OSError("sensor error"))
    def test_exception_returns_none(self, mock_cpu):
        self.assertIsNone(hardware._get_cpu_percent())

    @patch("hardware.psutil.cpu_percent", side_effect=RuntimeError("unexpected"))
    def test_runtime_exception_returns_none(self, mock_cpu):
        self.assertIsNone(hardware._get_cpu_percent())


class TestGetDiskMetrics(unittest.TestCase):
    """Tests for _get_disk_metrics."""

    @patch("hardware.psutil.disk_usage")
    def test_calculates_gb_correctly(self, mock_disk):
        disk = MagicMock()
        disk.percent = 80.0
        disk.used = 160 * 1024**3
        disk.total = 200 * 1024**3
        disk.free = 40 * 1024**3
        mock_disk.return_value = disk

        result = hardware._get_disk_metrics()
        self.assertEqual(result["disk_percent"], 80.0)
        self.assertAlmostEqual(result["disk_used_gb"], 160.0, places=1)
        self.assertAlmostEqual(result["disk_total_gb"], 200.0, places=1)
        self.assertAlmostEqual(result["disk_free_gb"], 40.0, places=1)

    @patch("hardware.psutil.disk_usage", side_effect=PermissionError("access denied"))
    def test_permission_error_returns_none_values(self, mock_disk):
        result = hardware._get_disk_metrics()
        self.assertIsNone(result["disk_percent"])
        self.assertIsNone(result["disk_used_gb"])
        self.assertIsNone(result["disk_total_gb"])
        self.assertIsNone(result["disk_free_gb"])


class TestGetRamMetrics(unittest.TestCase):
    """Tests for _get_ram_metrics."""

    @patch("hardware.psutil.virtual_memory")
    def test_returns_expected_fields(self, mock_vmem):
        mem = MagicMock()
        mem.percent = 45.0
        mem.used = 3 * 1024**3
        mem.total = 8 * 1024**3
        mock_vmem.return_value = mem

        result = hardware._get_ram_metrics()
        self.assertEqual(result["ram_percent"], 45.0)
        self.assertAlmostEqual(result["ram_used_gb"], 3.0, places=1)
        self.assertAlmostEqual(result["ram_total_gb"], 8.0, places=1)

    @patch("hardware.psutil.virtual_memory", side_effect=Exception("fail"))
    def test_exception_returns_none_values(self, mock_vmem):
        result = hardware._get_ram_metrics()
        self.assertIsNone(result["ram_percent"])
        self.assertIsNone(result["ram_used_gb"])
        self.assertIsNone(result["ram_total_gb"])


class TestGetUptimeSeconds(unittest.TestCase):
    """Tests for _get_uptime_seconds."""

    @patch("hardware.time.time", return_value=10000.0)
    @patch("hardware.psutil.boot_time", return_value=1000.0)
    def test_calculates_uptime(self, mock_boot, mock_time):
        result = hardware._get_uptime_seconds()
        self.assertAlmostEqual(result, 9000.0, places=0)

    @patch("hardware.psutil.boot_time", side_effect=Exception("no data"))
    def test_exception_returns_none(self, mock_boot):
        result = hardware._get_uptime_seconds()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
