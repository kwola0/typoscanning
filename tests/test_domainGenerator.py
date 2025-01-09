import unittest
from domainGenerator import (
    is_valid_domain, load_keyboard_proximity, load_tlds, generate_prefix_suffix_domains,
    generate_tld_replacements, generate_keyboard_proximity_domains,
    generate_visual_substitutions,
    generate_typo_domains, generate_removal_and_addition,
    generate_transposed_domains, generate_subdomain_domains,
    generate_hyphen_dot_manipulations
)

class TestDomainGenerator(unittest.TestCase):

    def test_is_valid_domain(self):
        self.assertTrue(is_valid_domain("example.com"))
        self.assertFalse(is_valid_domain("example..com"))
        self.assertFalse(is_valid_domain("-example.com"))

    def test_load_keyboard_proximity(self):
        keyboard_map = load_keyboard_proximity("lists/keyboard_proximity.txt")
        self.assertIsInstance(keyboard_map, dict)
        self.assertIn('a', keyboard_map)

    def test_load_tlds(self):
        tlds = load_tlds("lists/tlds_100.txt")
        self.assertIsInstance(tlds, list)
        self.assertIn('com', tlds)

    def test_generate_prefix_suffix_domains(self):
        prefixes_suffixes = ["test", "sample"]
        domains = generate_prefix_suffix_domains("example", "com", prefixes_suffixes)
        self.assertIn("test-example.com", domains)
        self.assertIn("example-sample.com", domains)

    def test_generate_tld_replacements(self):
        tlds = ["net", "org"]
        domains = generate_tld_replacements("example", "com", tlds)
        self.assertIn("example.net", domains)
        self.assertIn("example.org", domains)
        self.assertNotIn("example.com", domains)

    def test_generate_keyboard_proximity_domains(self):
        keyboard_map = {"a": ["q", "z"]}
        domains = generate_keyboard_proximity_domains("apple", "com", keyboard_map)
        self.assertIn("qpple.com", domains)
        self.assertIn("zpple.com", domains)

    def test_generate_visual_substitutions(self):
        similar_char_map = {"o": ["0"]}
        domains = generate_visual_substitutions("hello", "com", similar_char_map)
        self.assertIn("hell0.com", domains)

    def test_generate_removal_and_addition(self):
        domains = generate_removal_and_addition("example", "com")
        self.assertIn("xample.com", domains)
        self.assertIn("examplea.com", domains)

    def test_generate_transposed_domains(self):
        domains = generate_transposed_domains("example", "com")
        self.assertIn("eaxmple.com", domains)
        self.assertIn("exapmle.com", domains)

    def test_generate_subdomain_domains(self):
        subdomains = ["www", "mail"]
        domains = generate_subdomain_domains("example", "com", subdomains)
        self.assertIn("example.www.com", domains)
        self.assertIn("example.mail.com", domains)

    def test_generate_hyphen_dot_manipulations(self):
        domains = generate_hyphen_dot_manipulations("ex-ample", "com")
        self.assertIn("example.com", domains)
        self.assertIn("ex.ample.com", domains)

    def test_generate_typo_domains(self):
        tlds = ["net", "org"]
        similar_char_map = {"o": ["0"]}
        keyboard_map = {"a": ["q", "z"]}
        subdomains = ["www", "mail"]
        prefixes_suffixes = ["test", "sample"]

        domains = generate_typo_domains("example.com", tlds, similar_char_map, keyboard_map, subdomains, prefixes_suffixes)
        self.assertIsInstance(domains, list)
        self.assertTrue(any("test-example.com" in d for d in domains))
        self.assertTrue(any("example.net" in d for d in domains))

if __name__ == "__main__":
    unittest.main()
