import requests
from dotenv import load_dotenv
import os

load_dotenv()

VT_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")


def check_domain_reputation(domain, api_key):
    # Performs VT reputation check
    print(f"Checking reputation for domain: {domain}")
    url = f"https://www.virustotal.com/api/v3/domains/{domain}"
    headers = {"x-apikey": api_key}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            vt_data = response.json().get('data', {}).get('attributes', {})
            return {
                "domain": domain,
                "last_modification_date": vt_data.get("last_modification_date"),
                "whois": vt_data.get("whois"),
                "last_dns_records_date": vt_data.get("last_dns_records_date"),
                "last_https_certificate_date": vt_data.get("last_https_certificate_date"),
                "categories": vt_data.get("categories", {}),
                "reputation": vt_data.get("reputation"),
                "total_votes": vt_data.get("total_votes", {}),
                "tags": vt_data.get("tags", []),
                "last_analysis_stats": vt_data.get("last_analysis_stats", {})
            }
        else:
            print(f"Error: VirusTotal returned status code {response.status_code} for domain {domain}")
            return {"error": "Failed to retrieve data from VirusTotal"}
    except Exception as e:
        print(f"Error: Could not connect to VirusTotal for domain {domain}. Exception: {e}")
        return {"error": str(e)}
