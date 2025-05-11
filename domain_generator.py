import regex
from typing import List, Dict, Set
import jellyfish


def is_valid_domain(domain: str) -> bool:
    # Checks if a domain is valid, including Unicode characters for IDN
    domain_regex = r"^(?!-)[\p{L}\p{N}\-]{1,63}(?<!-)(\.[A-Za-z]{2,})+$"
    return regex.match(domain_regex, domain) is not None


def load_keyboard_proximity(file_path: str) -> Dict[str, List[str]]:
    # Loads keyboard proximity mappings from file
    keyboard_map = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.strip() and not line.startswith("//"):
                    key, values = line.strip().split(':')
                    keyboard_map[key] = values.split(',')
    except FileNotFoundError:
        print(f"Error: Keyboard proximity file not found: {file_path}")
    return keyboard_map


def load_tlds(file_path: str) -> List[str]:
    # Loads TLDs from file
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip().lstrip('.') for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: TLD file not found: {file_path}")
        return []


def load_subdomains(file_path: str) -> List[str]:
    # Loads subdomains from file
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: Subdomains file not found: {file_path}")
        return []


def load_prefixes_and_suffixes(file_path: str) -> List[str]:
    # Loads a list of prefixes and suffixes
    unique_entries = set()

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("//"):
                    continue

                unique_entries.add(line)

    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
    except Exception as e:
        print(f"Error while reading file: {e}")

    return list(unique_entries)


def load_similar_chars(file_path: str) -> Dict[str, List[str]]:
    # Loads visually similar characters mappings
    similar_char_map = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.strip() and not line.startswith("//"):
                    key, value = line.strip().split(',')
                    if key not in similar_char_map:
                        similar_char_map[key] = []
                    similar_char_map[key].append(value)
    except FileNotFoundError:
        print(f"Error: Similar characters file not found: {file_path}")
    return similar_char_map


def generate_soundsquatting_domains(main_name: str, base_tld: str) -> Set[str]:
    # Generates soundsquatting domains (more in \tests\soundsquatting_test.py)
    typo_domains = set()
    original_phonetic = jellyfish.metaphone(main_name)
    alphabet = 'abcdefghijklmnopqrstuvwxyz'

    for i in range(len(main_name)):
        typo_domains.add(main_name[:i] + main_name[i + 1:] + '.' + base_tld)
    for i in range(len(main_name)):
        for char in alphabet:
            typo_domains.add(main_name[:i] + char + main_name[i + 1:] + '.' + base_tld)
    for i in range(len(main_name) + 1):
        for char in alphabet:
            typo_domains.add(main_name[:i] + char + main_name[i:] + '.' + base_tld)

    return {
        typo for typo in typo_domains
        if jellyfish.metaphone(typo.split('.')[0]) == original_phonetic
    }


def generate_prefix_suffix_domains(main_name: str, base_tld: str, entries: List[str]) -> Set[str]:
    # Generates domains with given prefixes and suffixes
    typo_domains = set()
    for entry in entries:
        typo_domains.add(f"{entry}-{main_name}.{base_tld}")
        typo_domains.add(f"{main_name}-{entry}.{base_tld}")

    return typo_domains


def generate_tld_replacements(main_name: str, base_tld: str, tlds: List[str]) -> Set[str]:
    # Generates domains with replaced TLDs
    return {f"{main_name}.{tld}" for tld in tlds if tld != base_tld}


def generate_keyboard_proximity_domains(main_name: str, base_tld: str, keyboard_map: Dict[str, List[str]]) -> Set[str]:
    # Generates domains based on keyboard proximity substitutions
    typo_domains = set()
    for i, char in enumerate(main_name):
        if char in keyboard_map:
            for replacement in keyboard_map[char]:
                substituted = list(main_name)
                substituted[i] = replacement
                typo_domains.add("".join(substituted) + '.' + base_tld)

                typo_domains.add(main_name[:i] + replacement + main_name[i:] + '.' + base_tld)
                typo_domains.add(main_name[:i + 1] + replacement + main_name[i + 1:] + '.' + base_tld)
    return typo_domains


def generate_visual_substitutions(main_name: str, base_tld: str, similar_char_map: Dict[str, List[str]]) -> Set[str]:
    # Generates domains with visually similar character substitutions
    typo_domains = set()
    for i, char in enumerate(main_name):
        if char in similar_char_map:
            for replacement in similar_char_map[char]:
                substituted = list(main_name)
                substituted[i] = replacement
                typo_domains.add("".join(substituted) + '.' + base_tld)
    return typo_domains


def generate_removal_and_addition(main_name: str, base_tld: str) -> Set[str]:
    # Generates domains by removing and adding characters
    typo_domains = set()
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"

    for i in range(len(main_name)):
        typo_domains.add(main_name[:i] + main_name[i + 1:] + '.' + base_tld)

    for i in range(len(main_name) + 1):
        for char in alphabet:
            typo_domains.add(main_name[:i] + char + main_name[i:] + '.' + base_tld)
    return typo_domains


def generate_transposed_domains(main_name: str, base_tld: str) -> Set[str]:
    # Generates domains by transposing adjacent characters
    typo_domains = set()
    for i in range(len(main_name) - 1):
        swapped = list(main_name)
        swapped[i], swapped[i + 1] = swapped[i + 1], swapped[i]
        typo_domains.add("".join(swapped) + '.' + base_tld)
    return typo_domains


def generate_subdomain_domains(main_name: str, base_tld: str, subdomains: List[str]) -> Set[str]:
    # Generates domains with subdomains added
    return {f"{main_name}.{subdomain}.{base_tld}" for subdomain in subdomains}


def generate_hyphen_dot_manipulations(main_name: str, base_tld: str) -> Set[str]:
    # Generates domains by manipulating hyphens and dots
    typo_domains = set()
    if '-' in main_name:
        typo_domains.add(main_name.replace('-', '') + '.' + base_tld)
        typo_domains.add(main_name.replace('-', '.') + '.' + base_tld)
    if '.' in main_name:
        typo_domains.add(main_name.replace('.', '-') + '.' + base_tld)
    return typo_domains


def generate_bitsquatting_domains(main_name: str, base_tld: str) -> set:
    typo_domains = set()

    for i, char in enumerate(main_name):
        ascii_value = ord(char)
        for bit in range(8):
            flipped_value = ascii_value ^ (1 << bit)
            if 32 <= flipped_value <= 126:
                flipped_char = chr(flipped_value)
                new_domain = (main_name[:i] + flipped_char + main_name[i + 1:]).lower() + '.' + base_tld
                typo_domains.add(new_domain)

    return typo_domains


def generate_typo_domains(domain: str, tlds: List[str], similar_char_map: Dict[str, List[str]],
                          keyboard_map: Dict[str, List[str]], subdomains: List[str],
                          entries: List[str]) -> List[str]:
    # Generates all possible typosquatting domains
    typo_domains = set()

    domain_parts = domain.split('.')
    if len(domain_parts) < 2:
        print(f"Error: Invalid domain format: {domain}")
        return []

    main_name, base_tld = '.'.join(domain_parts[:-1]), domain_parts[-1]

    typo_domains |= generate_prefix_suffix_domains(main_name, base_tld, entries)
    typo_domains |= generate_tld_replacements(main_name, base_tld, tlds)
    typo_domains |= generate_keyboard_proximity_domains(main_name, base_tld, keyboard_map)
    typo_domains |= generate_visual_substitutions(main_name, base_tld, similar_char_map)
    typo_domains |= generate_removal_and_addition(main_name, base_tld)
    typo_domains |= generate_transposed_domains(main_name, base_tld)
    typo_domains |= generate_subdomain_domains(main_name, base_tld, subdomains)
    typo_domains |= generate_hyphen_dot_manipulations(main_name, base_tld)
    typo_domains |= generate_soundsquatting_domains(main_name, base_tld)
    typo_domains |= generate_bitsquatting_domains(main_name, base_tld)

    valid_domains = [d for d in typo_domains if is_valid_domain(d)]
    print(f"Generated {len(valid_domains)} valid typo domains.")
    return valid_domains
