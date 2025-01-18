import json
import os
from datetime import datetime

import jellyfish
from dotenv import load_dotenv

from alerts import alert_conditions
from dns_check import check_domain_exists, get_domain_ip
from domain_generator import (
    generate_typo_domains,
    load_tlds,
    load_subdomains,
    load_keyboard_proximity,
    load_prefixes_and_suffixes,
    load_similar_chars
)
from models import db, ScanHistory, Domain, ScanDetails
from reputation import check_domain_reputation
from whois_lookup import get_whois_info

load_dotenv()

VT_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")


def calculate_damerau_levenshtein_score(original_domain: str, domain: str) -> int:
    return jellyfish.damerau_levenshtein_distance(original_domain, domain)


def calculate_domain_similarity_in_percent(original_domain: str, domain: str) -> float:
    """ Returns the percentage similarity between two domain names.
    Uses the Damerau-Levenshtein distance and the average length of both name """
    distance = calculate_damerau_levenshtein_score(original_domain, domain)
    avg_len = (len(original_domain) + len(domain)) / 2

    if avg_len == 0:
        return 100.0

    similarity_raw = (avg_len - distance) / avg_len
    similarity_percent = similarity_raw * 100

    similarity_percent = max(min(similarity_percent, 100.0), 0.0)
    return round(similarity_percent, 2)


def quick_scan_domain(domain_name: str):
    # Performs quick scan, alerts and db write skipped

    print(f"[INFO] Starting Quick Scan for domain: {domain_name}")
    base_dir = os.path.join(os.path.dirname(__file__), "lists")

    try:
        tlds = load_tlds(os.path.join(base_dir, "tlds_100.txt"))
        subdomains = load_subdomains(os.path.join(base_dir, "subdomains.txt"))
        keyboard_map = load_keyboard_proximity(os.path.join(base_dir, "keyboard_proximity.txt"))
        entries = load_prefixes_and_suffixes(os.path.join(base_dir, "prefixes_suffixes.txt"))
        similar_chars = load_similar_chars(os.path.join(base_dir, "similar_chars.txt"))

        generated_domains = generate_typo_domains(domain_name, tlds, similar_chars, keyboard_map, subdomains, entries)
        valid_domains = [d for d in generated_domains if check_domain_exists(d)]
        print(f"[SUCCESS] Found {len(valid_domains)} existing domains.")

        domains_info = []
        analyzed_count = 0

        for valid_domain in valid_domains:
            whois_info = get_whois_info(valid_domain) or {}
            ip_address = get_domain_ip(valid_domain) or "---"
            score = calculate_damerau_levenshtein_score(domain_name, valid_domain)
            similarity_percent = calculate_domain_similarity_in_percent(domain_name, valid_domain)

            domain_data = {
                "domain": valid_domain,
                "ip_address": ip_address,
                "score": score,
                "similarity_percent": similarity_percent,
                "whois_info": {
                    "registrar": whois_info.get("registrar", "---"),
                    "country": whois_info.get("country", "---"),
                    "creation_date": whois_info.get("creation_date", "---"),
                    "expiration_date": whois_info.get("expiration_date", "---"),
                    "name_servers": whois_info.get("name_servers", "---"),
                    "emails": whois_info.get("emails", "---")
                }
            }
            # VirusTotal – limit 4 API requests per hour on free plan
            if score <= 1 and analyzed_count < 4:
                vt_result = check_domain_reputation(valid_domain, VT_API_KEY) or {}
                domain_data["vt_data"] = vt_result
                analyzed_count += 1
            else:
                domain_data["vt_link"] = f"https://www.virustotal.com/gui/domain/{valid_domain}"

            domains_info.append(domain_data)

        print(f"[SUCCESS] Processed {len(domains_info)} domains with {analyzed_count} VirusTotal analyses.")

        #Sorting by Similarity Score (%) in descending order
        domains_info = sorted(domains_info,
                              key=lambda x: x.get('similarity_percent', 0.0),
                              reverse=True)

        return {
            "domains": domains_info,
            "valid_domains": valid_domains,
            "generated_domains": generated_domains
        }

    except Exception as e:
        print(f"[ERROR] Quick scan failed: {e}")
        raise RuntimeError(f"Quick scan failed: {e}")


def full_scan_domain(domain: Domain):
    # Full scan for logged-in user
    print(f"[INFO] Starting Full Scan for domain: {domain.name}")
    base_dir = os.path.join(os.path.dirname(__file__), "lists")

    try:
        tlds = load_tlds(os.path.join(base_dir, "tlds_100.txt"))
        subdomains = load_subdomains(os.path.join(base_dir, "subdomains.txt"))
        keyboard_map = load_keyboard_proximity(os.path.join(base_dir, "keyboard_proximity.txt"))
        entries = load_prefixes_and_suffixes(os.path.join(base_dir, "prefixes_suffixes.txt"))
        similar_chars = load_similar_chars(os.path.join(base_dir, "similar_chars.txt"))

        generated_domains = generate_typo_domains(
            domain.name, tlds, similar_chars, keyboard_map, subdomains, entries
        )
        valid_domains = [d for d in generated_domains if check_domain_exists(d)]
        print(f"[SUCCESS] Found {len(valid_domains)} existing domains.")

        domains_info = []
        analyzed_count = 0

        for valid_domain in valid_domains:
            whois_info = get_whois_info(valid_domain) or {}
            ip_address = get_domain_ip(valid_domain) or "---"

            score = calculate_damerau_levenshtein_score(domain.name, valid_domain)
            similarity_percent = calculate_domain_similarity_in_percent(domain.name, valid_domain)

            domain_data = {
                "domain": valid_domain,
                "ip_address": ip_address,
                "score": score,
                "similarity_percent": similarity_percent,
                "whois_info": {
                    "registrar": whois_info.get("registrar", "---"),
                    "country": whois_info.get("country", "---"),
                    "creation_date": whois_info.get("creation_date", "---"),
                    "expiration_date": whois_info.get("expiration_date", "---"),
                    "name_servers": whois_info.get("name_servers", "---"),
                    "emails": whois_info.get("emails", "---")
                }
            }

            # VirusTotal – limit 4 API requests per hour on free plan
            if score <= 1 and analyzed_count < 4:
                vt_result = check_domain_reputation(valid_domain, VT_API_KEY) or {}
                domain_data["vt_data"] = vt_result
                analyzed_count += 1
            else:
                domain_data["vt_link"] = f"https://www.virustotal.com/gui/domain/{valid_domain}"

            domains_info.append(domain_data)

        print(f"[SUCCESS] Processed {len(domains_info)} domains "
              f"with {analyzed_count} VirusTotal analyses.")

        domains_info = sorted(domains_info,
                              key=lambda x: x.get('similarity_percent', 0.0),
                              reverse=True)
        print("[INFO] Domains sorted by Similarity Score (%) in descending order.")

        alerted_domains = []
        last_scan_date = datetime.utcnow()
        try:
            alerted_domains = alert_conditions(domains_info, last_scan_date)
        except Exception as alert_error:
            print(f"[ERROR] Failed to determine alerts: {alert_error}")
            alerted_domains = []

        if not isinstance(alerted_domains, list):
            alerted_domains = []

        print(f"[ALERT] Alerted domains: {alerted_domains}")

        # db write ScanHistory
        new_scan = ScanHistory(
            domain_id=domain.id,
            date=datetime.utcnow(),
            permutations_checked=len(generated_domains),
            existing_domains=len(valid_domains),
            domains_alerted=json.dumps(alerted_domains)
        )
        db.session.add(new_scan)
        db.session.commit()

        # db write ScanDetails
        for info in domains_info:
            vt_data = info.get("vt_data", {})
            reputation = vt_data.get("reputation", "---")
            detail = ScanDetails(
                scan_id=new_scan.id,
                domain_name=info["domain"],
                ip_address=info["ip_address"],
                whois_name_servers=info["whois_info"].get("name_servers", "---"),
                whois_registrar=info["whois_info"].get("registrar", "---"),
                whois_country=info["whois_info"].get("country", "---"),
                whois_creation_date=info["whois_info"].get("creation_date", "---"),
                whois_emails=info["whois_info"].get("emails", "---"),
                similarity_score=info["similarity_percent"],
                reputation=reputation
            )
            db.session.add(detail)

        db.session.commit()
        print("[SUCCESS] Full scan results saved to database.")

    except Exception as e:
        print(f"[ERROR] Full scan failed: {e}")
        raise RuntimeError(f"Full scan failed: {e}")
