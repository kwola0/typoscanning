from datetime import datetime
from models import Whitelist


def alert_conditions(domains_info, last_scan_date):

    alerted_domains = []
    whitelisted_domains = [entry.whitelisted_domain for entry in Whitelist.query.all()]

    print(f"[DEBUG] Whitelisted domains: {whitelisted_domains}")

    for entry in domains_info:
        domain_name = entry.get("domain", "unknown-domain")
        if domain_name in whitelisted_domains:
            print(f"[INFO] {domain_name} is on WL, alert skipped.")
            continue

        whois_info = entry.get("whois_info", {})
        vt_data = entry.get("vt_data", {})
        reputation = vt_data.get("reputation", 0)
        score = entry.get("score", 0)

        # Condition 1: creation_date > last_scan_date ---
        creation_date_str = whois_info.get("creation_date", "")
        if creation_date_str not in ("", "---"):
            try:
                creation_date_obj = datetime.strptime(creation_date_str, "%Y-%m-%d")
                if creation_date_obj > last_scan_date:
                    alerted_domains.append(domain_name)
                    continue
            except ValueError:
                pass

        # Condition 2: (score <= 2) or (reputation > 2) ---
        if score <= 2 or reputation > 0:
            alerted_domains.append(domain_name)

    return alerted_domains
