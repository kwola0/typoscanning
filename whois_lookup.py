import datetime
import whois
from datetime import datetime


def get_whois_info(domain_name):

    if not isinstance(domain_name, str):
        raise ValueError(f"Expected string for domain_name, got {type(domain_name)}")

    try:
        domain_info = whois.whois(domain_name)
        name_servers = domain_info.name_servers
        if isinstance(name_servers, list):
            name_servers = ", ".join(name_servers)
        elif isinstance(name_servers, str):
            pass
        else:
            name_servers = "---"
        return {
            "domain_name": domain_name,
            "creation_date": str(domain_info.creation_date) if domain_info.creation_date else "---",
            "expiration_date": str(domain_info.expiration_date) if domain_info.expiration_date else "---",
            "name_servers": name_servers,
            "registrar": str(domain_info.registrar) if domain_info.registrar else "---",
            "emails": str(domain_info.emails) if domain_info.emails else "---",
            "country": str(domain_info.country) if domain_info.country else "---"
        }
    except Exception as e:
        print(f"[ERROR] WHOIS lookup failed for {domain_name}: {e}")
        return {
            "domain_name": domain_name,
            "creation_date": "---",
            "expiration_date": "---",
            "name_servers": "---",
            "registrar": "---",
            "emails": "---",
            "country": "---"
        }
        print(f"[INFO] WHOIS data collected for {domain_name}.")
        return whois_data

    except Exception as e:
        print(f"[ERROR] Error fetching WHOIS for {domain_name}: {e}")
        return {"error": str(e)}

def format_whois_date(date):

    if isinstance(date, list):
        return ", ".join(d.strftime('%Y-%m-%d %H:%M:%S') for d in date if isinstance(d, datetime))
    elif isinstance(date, datetime):
        return date.strftime('%Y-%m-%d %H:%M:%S')
    return "---"

def display_whois_info(whois_data):
    """
    Display WHOIS data in a readable format.
    """
    print("\nWHOIS Information:")
    print(f"Domain Name: {whois_data.get('domain_name', '---')}")
    print(f"Registrar: {whois_data.get('registrar', '---')}")
    print(f"Country: {whois_data.get('country', '---')}")
    print(f"Creation Date: {format_whois_date(whois_data.get('creation_date'))}")
    print(f"Expiration Date: {format_whois_date(whois_data.get('expiration_date'))}")
    print(f"Name Servers: {whois_data.get('name_servers', '---')}")
    print(f"Emails: {whois_data.get('emails', '---')}")
    print("-" * 50)


def main():

    domain_name = input("Enter a domain name to check WHOIS information: ").strip()
    if not domain_name:
        print("[ERROR] Domain name cannot be empty.")
        return

    whois_data = get_whois_info(domain_name)
    if "error" in whois_data:
        print(f"[ERROR] {whois_data['error']}")
        return

    display_whois_info(whois_data)


if __name__ == "__main__":
    main()
