import unittest
from unittest.mock import patch
import socket
from dns_check import check_domain_exists, get_domain_ip


class TestDNSCheck(unittest.TestCase):

    @patch('socket.gethostbyname')
    def test_check_domain_exists_valid(self, mock_gethostbyname):
        mock_gethostbyname.return_value = '93.184.216.34'
        result = check_domain_exists('example.com')
        self.assertTrue(result)
        mock_gethostbyname.assert_called_once_with('example.com')

    @patch('socket.gethostbyname', side_effect=socket.gaierror)
    def test_check_domain_exists_invalid(self, mock_gethostbyname):
        result = check_domain_exists('invalid-domain-12345.tld')
        self.assertFalse(result)
        mock_gethostbyname.assert_called_once_with('invalid-domain-12345.tld')

    @patch('socket.gethostbyname')
    def test_get_domain_ip_valid(self, mock_gethostbyname):
        mock_gethostbyname.return_value = '93.184.216.34'
        ip = get_domain_ip('example.com')
        self.assertEqual(ip, '93.184.216.34')
        mock_gethostbyname.assert_called_once_with('example.com')

    @patch('socket.gethostbyname', side_effect=socket.gaierror)
    def test_get_domain_ip_invalid(self, mock_gethostbyname):
        ip = get_domain_ip('invalid-domain-12345.tld')
        self.assertEqual(ip, 'N/A')
        mock_gethostbyname.assert_called_once_with('invalid-domain-12345.tld')

    @patch('socket.gethostbyname', side_effect=Exception('Unexpected error'))
    def test_get_domain_ip_unexpected_error(self, mock_gethostbyname):
        ip = get_domain_ip('example.com')
        self.assertEqual(ip, 'N/A')
        mock_gethostbyname.assert_called_once_with('example.com')


if __name__ == '__main__':
    unittest.main()
