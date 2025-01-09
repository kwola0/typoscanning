import unittest
from unittest.mock import patch
from reputation import check_domain_reputation

class TestVirusTotal(unittest.TestCase):

    @patch("requests.get")
    def test_check_domain_reputation_success(self, mock_get):
        mock_response = {
            "data": {
                "attributes": {
                    "last_modification_date": "2025-01-01",
                    "whois": "Sample WHOIS data",
                    "last_dns_records_date": "2025-01-01",
                    "last_https_certificate_date": "2025-01-01",
                    "categories": {"malicious": "example"},
                    "reputation": -10,
                    "total_votes": {"harmless": 10, "malicious": 2},
                    "tags": ["phishing", "malware"],
                    "last_analysis_stats": {"malicious": 1, "harmless": 5}
                }
            }
        }

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        api_key = "test_api_key"
        result = check_domain_reputation("example.com", api_key)

        self.assertEqual(result["domain"], "example.com")
        self.assertEqual(result["reputation"], -10)
        self.assertIn("phishing", result["tags"])
        self.assertEqual(result["last_analysis_stats"], {"malicious": 1, "harmless": 5})

    @patch("requests.get")
    def test_check_domain_reputation_failure(self, mock_get):
        mock_get.return_value.status_code = 404

        api_key = "test_api_key"
        result = check_domain_reputation("nonexistent.com", api_key)

        self.assertIn("error", result)
        self.assertEqual(result["error"], "Failed to retrieve data from VirusTotal")

    @patch("requests.get", side_effect=Exception("Connection error"))
    def test_check_domain_reputation_exception(self, mock_get):
        api_key = "test_api_key"
        result = check_domain_reputation("example.com", api_key)

        self.assertIn("error", result)
        self.assertEqual(result["error"], "Connection error")

if __name__ == "__main__":
    unittest.main()
