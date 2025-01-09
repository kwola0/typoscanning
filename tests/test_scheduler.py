import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

class TestScheduler(unittest.TestCase):


    def test_check_custom_cron(self):
        from scheduler import check_custom_cron
        cron_expression = "invalid-cron"
        current_time = datetime(2025, 1, 1, 7, 0)
        result = check_custom_cron(cron_expression, current_time)
        self.assertFalse(result)

    @patch("scheduler.full_scan_domain")
    def test_perform_full_scan(self, mock_full_scan):
        from scheduler import perform_full_scan
        mock_domain = MagicMock(name="example.com")

        perform_full_scan(mock_domain)

        mock_full_scan.assert_called_once_with(mock_domain)

if __name__ == "__main__":
    unittest.main()
