import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app import app
from alerts import alert_conditions

class TestAlertConditions(unittest.TestCase):

    @patch("app.db.session.query")
    def test_alert_conditions(self, mock_query):
        # Mock whitelist query result
        mock_query.return_value.filter.return_value.all.return_value = [
            MagicMock(whitelisted_domain="clean-domain.com")
        ]

        # Test data
        domains_info = [
            {
                "domain": "alerted-domain1.com",
                "whois_info": {"creation_date": "2025-01-10"},
                "vt_data": {"reputation": 5},
                "score": 1
            },
            {
                "domain": "clean-domain.com",
                "whois_info": {"creation_date": "2023-01-01"},
                "vt_data": {"reputation": 0},
                "score": 5
            },
            {
                "domain": "alerted-domain2.com",
                "whois_info": {"creation_date": "2024-12-15"},
                "vt_data": {"reputation": 6},
                "score": 2
            },
            {
                "domain": "invalid-date-domain.com",
                "whois_info": {"creation_date": "invalid-date"},
                "vt_data": {"reputation": 7},
                "score": 1
            }
        ]

        last_scan_date = datetime.strptime("2024-01-01", "%Y-%m-%d")

        # Use Flask app context
        with app.app_context():
            alerted_domains = alert_conditions(domains_info, last_scan_date)

        # Assertions
        self.assertIn("alerted-domain1.com", alerted_domains)
        self.assertIn("alerted-domain2.com", alerted_domains)
        self.assertNotIn("clean-domain.com", alerted_domains)
        self.assertIn("invalid-date-domain.com", alerted_domains)


if __name__ == "__main__":
    unittest.main()
