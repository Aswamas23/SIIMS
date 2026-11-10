"""
Unit tests for software.py.
Mocks the winreg module to test on non-Windows platforms.
The conftest.py provides a stub winreg in sys.modules before software is imported.
"""
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# Import software at module level (conftest ensures monitoring-agent is on sys.path
# and injects a fake winreg before this import happens)
import software


class TestParseSoftwareDate(unittest.TestCase):
    """Tests for _parse_install_date()."""

    def test_valid_yyyymmdd(self):
        self.assertEqual(software._parse_install_date("20230115"), "2023-01-15")

    def test_last_day_of_year(self):
        self.assertEqual(software._parse_install_date("20001231"), "2000-12-31")

    def test_latest_date(self):
        self.assertEqual(software._parse_install_date("20240830"), "2024-08-30")

    def test_none_returns_none(self):
        self.assertIsNone(software._parse_install_date(None))

    def test_empty_string_returns_none(self):
        self.assertIsNone(software._parse_install_date(""))

    def test_non_digit_returns_none(self):
        self.assertIsNone(software._parse_install_date("not-a-date"))

    def test_slash_format_returns_none(self):
        self.assertIsNone(software._parse_install_date("2023/01/15"))

    def test_too_short_returns_none(self):
        self.assertIsNone(software._parse_install_date("202301"))

    def test_whitespace_stripped(self):
        # Whitespace padded but still valid
        self.assertEqual(software._parse_install_date("  20230115  "), "2023-01-15")


class TestDeduplication(unittest.TestCase):
    """Tests for _deduplicate()."""

    def test_removes_exact_duplicate(self):
        entries = [
            {"name": "App A", "publisher": "Vendor", "version": "1.0", "install_date": None},
            {"name": "App A", "publisher": "Vendor", "version": "1.0", "install_date": None},
        ]
        result = software._deduplicate(entries)
        self.assertEqual(len(result), 1)

    def test_keeps_different_versions(self):
        entries = [
            {"name": "App A", "publisher": "Vendor", "version": "1.0", "install_date": None},
            {"name": "App A", "publisher": "Vendor", "version": "2.0", "install_date": None},
        ]
        result = software._deduplicate(entries)
        self.assertEqual(len(result), 2)

    def test_case_insensitive_dedup(self):
        entries = [
            {"name": "App A", "publisher": "Vendor", "version": "1.0", "install_date": None},
            {"name": "app a", "publisher": "vendor", "version": "1.0", "install_date": None},
        ]
        result = software._deduplicate(entries)
        self.assertEqual(len(result), 1)

    def test_empty_list(self):
        self.assertEqual(software._deduplicate([]), [])

    def test_no_duplicates(self):
        entries = [
            {"name": "App A", "publisher": "X", "version": "1", "install_date": None},
            {"name": "App B", "publisher": "Y", "version": "2", "install_date": None},
        ]
        result = software._deduplicate(entries)
        self.assertEqual(len(result), 2)

    def test_preserves_first_occurrence(self):
        entries = [
            {"name": "App", "publisher": "Pub", "version": "1.0", "install_date": "2024-01-01"},
            {"name": "App", "publisher": "Pub", "version": "1.0", "install_date": "2023-05-05"},
        ]
        result = software._deduplicate(entries)
        self.assertEqual(len(result), 1)
        # First occurrence (2024-01-01) must be kept
        self.assertEqual(result[0]["install_date"], "2024-01-01")


class TestCollectSoftwareNotWindows(unittest.TestCase):
    """Tests for collect_software() on non-Windows (winreg unavailable)."""

    def test_returns_empty_list_when_winreg_unavailable(self):
        with patch.object(software, "_WINREG_AVAILABLE", False):
            result = software.collect_software()
        self.assertEqual(result, [])
        self.assertIsInstance(result, list)


class TestCollectSoftwareWithMockedRegistry(unittest.TestCase):
    """Tests for collect_software() with winreg stubbed out."""

    def test_returns_empty_list_when_all_paths_fail(self):
        """When all registry path opens fail, return an empty list."""
        with patch.object(software, "_WINREG_AVAILABLE", True):
            with patch.object(software, "_scan_registry_path", return_value=[]):
                result = software.collect_software()
        self.assertIsInstance(result, list)

    def test_deduplicates_across_registry_paths(self):
        """Identical entries from different registry paths appear only once."""
        duplicate_entries = [
            {"name": "App A", "publisher": "Vendor", "version": "1.0", "install_date": None},
            {"name": "App A", "publisher": "Vendor", "version": "1.0", "install_date": None},
            {"name": "App B", "publisher": "Other", "version": "2.0", "install_date": None},
        ]

        # _scan_registry_path is called 3 times (once per path); each returns duplicates
        with patch.object(software, "_WINREG_AVAILABLE", True):
            with patch.object(software, "_scan_registry_path", return_value=duplicate_entries[:]):
                result = software.collect_software()

        # 3 paths × 3 entries = 9 raw, but after dedup: App A (1) + App B (1) = 2
        self.assertEqual(len(result), 2)
        names = [e["name"] for e in result]
        self.assertIn("App A", names)
        self.assertIn("App B", names)

    def test_result_entries_have_required_keys(self):
        """Each entry in the result must have name, publisher, version, install_date."""
        fake_entries = [
            {"name": "Test App", "publisher": "ACME", "version": "3.1.4", "install_date": "2024-01-01"},
        ]
        with patch.object(software, "_WINREG_AVAILABLE", True):
            with patch.object(software, "_scan_registry_path", return_value=fake_entries):
                result = software.collect_software()

        self.assertGreater(len(result), 0)
        for entry in result:
            for key in ("name", "publisher", "version", "install_date"):
                self.assertIn(key, entry, f"Key '{key}' missing from entry: {entry}")

    def test_entire_function_exception_returns_empty_list(self):
        """If _scan_registry_path raises, collect_software returns [] without raising."""
        with patch.object(software, "_WINREG_AVAILABLE", True):
            with patch.object(software, "_scan_registry_path", side_effect=Exception("unexpected")):
                result = software.collect_software()
        self.assertEqual(result, [])


class TestReadStringValue(unittest.TestCase):
    """Tests for _read_string_value() helper."""

    def test_returns_string_value(self):
        """REG_SZ value should be returned as a stripped string."""
        # Build a fake winreg with QueryValueEx
        fake_winreg = types.ModuleType("winreg")
        fake_winreg.REG_SZ = 1
        fake_winreg.REG_EXPAND_SZ = 2

        def fake_query(key, name):
            return ("  Test Value  ", 1)

        fake_winreg.QueryValueEx = fake_query
        sys.modules["winreg"] = fake_winreg

        # Temporarily replace software's _winreg reference
        with patch.object(software, "_winreg", fake_winreg):
            with patch.object(software, "_WINREG_AVAILABLE", True):
                result = software._read_string_value(MagicMock(), "DisplayName")

        self.assertEqual(result, "Test Value")
        sys.modules.pop("winreg", None)

    def test_missing_value_returns_none(self):
        """FileNotFoundError from QueryValueEx should return None."""
        fake_winreg = types.ModuleType("winreg")
        fake_winreg.REG_SZ = 1
        fake_winreg.REG_EXPAND_SZ = 2
        fake_winreg.QueryValueEx = MagicMock(side_effect=FileNotFoundError)
        sys.modules["winreg"] = fake_winreg

        with patch.object(software, "_winreg", fake_winreg):
            with patch.object(software, "_WINREG_AVAILABLE", True):
                result = software._read_string_value(MagicMock(), "MissingKey")

        self.assertIsNone(result)
        sys.modules.pop("winreg", None)

    def test_empty_string_returns_none(self):
        """An empty REG_SZ value should be treated as None."""
        fake_winreg = types.ModuleType("winreg")
        fake_winreg.REG_SZ = 1
        fake_winreg.REG_EXPAND_SZ = 2
        fake_winreg.QueryValueEx = MagicMock(return_value=("", 1))
        sys.modules["winreg"] = fake_winreg

        with patch.object(software, "_winreg", fake_winreg):
            with patch.object(software, "_WINREG_AVAILABLE", True):
                result = software._read_string_value(MagicMock(), "DisplayName")

        self.assertIsNone(result)
        sys.modules.pop("winreg", None)


if __name__ == "__main__":
    unittest.main()
