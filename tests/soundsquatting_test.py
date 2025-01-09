import re
import jellyfish
from typing import List


def is_valid_domain(domain: str) -> bool:
    domain_regex = r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z]{2,})+$"
    return re.match(domain_regex, domain) is not None


def generate_soundsquatting_domains(domain: str) -> List[str]:
    typo_domains = set()
    domain_parts = domain.split('.')

    if len(domain_parts) < 2:
        print(f"Error: Invalid domain format: {domain}")
        return []

    main_name, base_tld = '.'.join(domain_parts[:-1]), domain_parts[-1]
    original_phonetic = jellyfish.metaphone(main_name)

    print(f"Original phonetic key: {original_phonetic}")

    alphabet = 'abcdefghijklmnopqrstuvwxyz'

    # Delete letter
    for i in range(len(main_name)):
        typo_domains.add(main_name[:i] + main_name[i + 1:] + '.' + base_tld)

    # Change letter
    for i in range(len(main_name)):
        for char in alphabet:
            typo_domains.add(main_name[:i] + char + main_name[i + 1:] + '.' + base_tld)

    # Add letter
    for i in range(len(main_name) + 1):
        for char in alphabet:
            typo_domains.add(main_name[:i] + char + main_name[i:] + '.' + base_tld)

    # Filter by phonetic key
    filtered_domains = set()
    for typo in typo_domains:
        typo_main = typo.split('.')[0]
        typo_phonetic = jellyfish.metaphone(typo_main)
        if typo_phonetic == original_phonetic:
            filtered_domains.add(typo)

    # Validate
    valid_domains = [d for d in filtered_domains if is_valid_domain(d)]
    print(f"Generated {len(valid_domains)} valid soundsquatting domains.")
    return valid_domains


if __name__ == "__main__":
    domain = "example.com"
    typo_domains = generate_soundsquatting_domains(domain)
    print("Sample generated soundsquatting domains:")
    for d in list(typo_domains)[:100]:
        print(d)
