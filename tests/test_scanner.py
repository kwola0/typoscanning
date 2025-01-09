import unittest
from unittest.mock import patch
from scanner import (quick_scan_domain,calculate_damerau_levenshtein_score, calculate_domain_similarity_in_percent)


class TestScanner(unittest.TestCase):

    def test_calculate_damerau_levenshtein_score(self):
        score = calculate_damerau_levenshtein_score("example.com", "exampel.com")
        self.assertEqual(score, 1)

        score = calculate_damerau_levenshtein_score("example.com", "example.org")
        self.assertEqual(score, 3)

    def test_calculate_domain_similarity_in_percent(self):
        similarity = calculate_domain_similarity_in_percent("example.com", "exampel.com")
        self.assertGreater(similarity, 80)

        similarity = calculate_domain_similarity_in_percent("example.com", "different.com")
        self.assertLess(similarity, 50)

    @patch("scanner.generate_typo_domains", return_value=["exampel.com", "example.org"])
    @patch("scanner.check_domain_exists", side_effect=lambda domain: domain == "example.org")
    @patch("scanner.get_whois_info", return_value={"registrar": "Example Registrar", "country": "US"})
    @patch("scanner.get_domain_ip", return_value="93.184.216.34")
    @patch("scanner.check_domain_reputation", return_value={"reputation": 5})
    def test_quick_scan_domain(self, mock_reputation, mock_get_ip, mock_whois, mock_check_exists, mock_generate):
        result = quick_scan_domain("example.com")

        self.assertIn("domains", result)
        self.assertEqual(len(result["valid_domains"]), 1)
        self.assertEqual(result["valid_domains"], ["example.org"])




if __name__ == "__main__":
    unittest.main()
