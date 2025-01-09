import unittest
from unittest.mock import patch, MagicMock
from whois_lookup import get_whois_info, format_whois_date, display_whois_info
from datetime import datetime

class TestWhoisLookup(unittest.TestCase):

    @patch("whois.whois")
    def test_get_whois_info_success(self, mock_whois):
        mock_whois.return_value = MagicMock(
            creation_date=datetime(2023, 1, 1),
            expiration_date=datetime(2025, 1, 1),
            name_servers=["ns1.example.com", "ns2.example.com"],
            registrar="Example Registrar",
            emails="admin@example.com",
            country="US"
        )

        result = get_whois_info("example.com")
        self.assertEqual(result["domain_name"], "example.com")
        self.assertEqual(result["creation_date"], "2023-01-01 00:00:00")
        self.assertEqual(result["expiration_date"], "2025-01-01 00:00:00")
        self.assertEqual(result["name_servers"], "ns1.example.com, ns2.example.com")
        self.assertEqual(result["registrar"], "Example Registrar")
        self.assertEqual(result["emails"], "admin@example.com")
        self.assertEqual(result["country"], "US")

    @patch("whois.whois", side_effect=Exception("WHOIS lookup failed"))
    def test_get_whois_info_failure(self, mock_whois):
        result = get_whois_info("example.com")
        self.assertEqual(result["domain_name"], "example.com")
        self.assertEqual(result["creation_date"], "---")
        self.assertEqual(result["expiration_date"], "---")
        self.assertEqual(result["name_servers"], "---")
        self.assertEqual(result["registrar"], "---")
        self.assertEqual(result["emails"], "---")
        self.assertEqual(result["country"], "---")

    def test_format_whois_date_single_date(self):
        date = datetime(2023, 1, 1, 12, 0, 0)
        formatted_date = format_whois_date(date)
        self.assertEqual(formatted_date, "2023-01-01 12:00:00")

    def test_format_whois_date_list_of_dates(self):
        dates = [datetime(2023, 1, 1, 12, 0, 0), datetime(2024, 1, 1, 12, 0, 0)]
        formatted_date = format_whois_date(dates)
        self.assertEqual(formatted_date, "2023-01-01 12:00:00, 2024-01-01 12:00:00")

    def test_format_whois_date_invalid(self):
        formatted_date = format_whois_date(None)
        self.assertEqual(formatted_date, "---")

    @patch("builtins.print")
    def test_display_whois_info(self, mock_print):
        whois_data = {
            "domain_name": "example.com",
            "registrar": "Example Registrar",
            "country": "US",
            "name_servers": "ns1.example.com, ns2.example.com",
            "emails": "admin@example.com"
        }

        display_whois_info(whois_data)

        mock_print.assert_any_call("\nWHOIS Information:")
        mock_print.assert_any_call("Domain Name: example.com")
        mock_print.assert_any_call("Registrar: Example Registrar")
        mock_print.assert_any_call("Country: US")
        mock_print.assert_any_call("Name Servers: ns1.example.com, ns2.example.com")
        mock_print.assert_any_call("Emails: admin@example.com")


if __name__ == "__main__":
    unittest.main()
