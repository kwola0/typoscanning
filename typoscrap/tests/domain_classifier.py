import os
import sys
import json
import requests
import socket
import ssl
from urllib.parse import urlparse
from dotenv import load_dotenv
from domain_generator import (
    generate_typo_domains,
    load_tlds,
    load_subdomains,
    load_keyboard_proximity,
    load_prefixes_and_suffixes,
    load_similar_chars
)
from dns_check import check_domain_exists

# Ładowanie zmiennych środowiskowych
load_dotenv()

# Bardzo rozbudowane heurystyki klasyfikacji (rozbudowano istniejące kategorie)
HEURISTICS = {
    "authoritative": {"keywords": ["przekierowuje", "redirect", "oryginalna domena", "original domain", "official website", "verified", "secure connection", "trusted", "certified", "authorized", "official page", "university website", "government site"], "group": "L"},
    "coinciding": {"keywords": ["treść legalna", "informacje", "legal content", "news", "information", "about us", "contact us", "homepage", "services", "products", "company", "team", "portfolio", "solutions", "press releases", "updates", "announcements", "legal notice"], "group": "L"},
    "protected": {"keywords": ["literówka", "typo", "niepoprawna nazwa", "check spelling", "did you mean", "did you mistype", "wrong domain", "incorrect domain", "possible typo", "common misspelling", "did you intend"], "group": "L"},
    "ad_parking": {"keywords": ["reklamy", "PPC", "kliknij tutaj", "banner", "ad parking", "buy this domain", "advertisement", "ad listings", "sponsored links", "ad network", "ads by google", "sponsored results", "advertorial"], "group": "M"},
    "adult_content": {"keywords": ["porno", "adult", "erotic", "xxx", "sex", "nude", "camgirl", "live cams", "adult dating", "18+", "explicit", "hardcore", "fetish", "escort", "naughty"], "group": "M"},
    "affiliate_abuse": {"keywords": ["afiliacyjny", "affiliate", "buy now", "limited offer", "sponsored", "referral", "special offer", "promo code", "earn commission", "affiliate link", "click to earn", "referral bonus", "get paid"], "group": "M"},
    "for_sale": {"keywords": ["na sprzedaż", "sprzedam", "for sale", "buy domain", "domain for sale", "purchase this domain", "available for purchase", "acquire this domain", "make an offer", "domain marketplace"], "group": "M"},
    "hit_stealing": {"keywords": ["traffic stealing", "redirect traffic", "moving you", "taking you to", "redirecting", "forwarding traffic", "this page redirects", "visitor redirection"], "group": "M"},
    "scam": {"keywords": ["oszustwo", "fraud", "download", "malware", "phishing", "your account", "verify your identity", "bank login", "urgent action required", "suspicious activity", "unauthorized access", "identity theft", "account recovery", "fake invoice", "security alert"], "group": "M"},
    "no_content": {"keywords": ["no content", "empty", "brak treści", "pusta strona", "under construction", "coming soon", "website under development", "maintenance mode", "page under construction", "no website configured", "placeholder page"], "group": "U"},
    "server_error": {"keywords": ["błąd serwera", "404", "500", "Internal Server Error", "page not found", "bad gateway", "unavailable", "502", "503", "504", "error 403", "forbidden", "connection refused"], "group": "U"},
    "crawl_error": {"keywords": [], "group": "U"},
    "other": {"keywords": [], "group": "U"}
}

def fetch_page(url):
    try:
        response = requests.get(url, timeout=10)
        return response.text, response.status_code
    except Exception:
        return None, None

def check_certificate(url):
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname or parsed.scheme != "https":
        return False
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
        san = cert.get('subjectAltName', ())
        dns_names = [name for typ, name in san if typ == 'DNS']
        common_names = []
        for tup in cert.get('subject', ()):  # type: ignore
            for key, value in tup:
                if key == 'commonName':
                    common_names.append(value)
        return hostname in dns_names or hostname in common_names
    except Exception:
        return False

def classify_content(content, status_code, cert_valid):
    if status_code is None or status_code >= 400:
        return "crawl_error", HEURISTICS["crawl_error"]["group"]
    if not content or len(content.strip()) < 50:
        return "no_content", HEURISTICS["no_content"]["group"]

    text = content.lower()
    suspicious_cert = not cert_valid

    for category, config in HEURISTICS.items():
        for keyword in config["keywords"]:
            if keyword.lower() in text:
                if category == "authoritative" and suspicious_cert:
                    return "protected", HEURISTICS["protected"]["group"]
                return category, config["group"]

    return ("protected", HEURISTICS["protected"]["group"]) if suspicious_cert else ("coinciding", HEURISTICS["coinciding"]["group"])

def process_domain(base_domain, output_file):
    print(f"[INFO] Starting typo-scan for: {base_domain}")

    base_dir = os.path.join(os.path.dirname(__file__), "lists")
    tlds = load_tlds(os.path.join(base_dir, "tlds_100.txt"))
    subdomains = load_subdomains(os.path.join(base_dir, "subdomains.txt"))
    keyboard_map = load_keyboard_proximity(os.path.join(base_dir, "keyboard_proximity.txt"))
    entries = load_prefixes_and_suffixes(os.path.join(base_dir, "prefixes_suffixes.txt"))
    similar_chars = load_similar_chars(os.path.join(base_dir, "similar_chars.txt"))

    generated_domains = generate_typo_domains(base_domain, tlds, similar_chars, keyboard_map, subdomains, entries)

    print(f"[INFO] Generated {len(generated_domains)} typo domains.")

    existing_domains = [d for d in generated_domains if check_domain_exists(d)]

    print(f"[INFO] Found {len(existing_domains)} existing domains.")

    for domain in existing_domains:
        url = "https://" + domain
        cert_valid = check_certificate(url)
        content, status_code = fetch_page(url)
        category, group = classify_content(content, status_code, cert_valid)
        result = {
            "base_domain": base_domain,
            "domain": domain,
            "status_code": status_code,
            "cert_valid": cert_valid,
            "category": category,
            "group": group
        }
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_and_scrape.py domain.com or domains.txt")
        sys.exit(1)

    input_value = sys.argv[1]
    output_file = "scrape_results.jsonl"

    if os.path.exists(output_file):
        os.remove(output_file)

    if input_value.endswith(".txt") and os.path.isfile(input_value):
        with open(input_value, "r", encoding="utf-8") as f:
            domains = [line.strip() for line in f if line.strip()]
        for domain in domains:
            process_domain(domain, output_file)
    else:
        process_domain(input_value, output_file)

    print(f"[SUCCESS] Results saved to {output_file}")
