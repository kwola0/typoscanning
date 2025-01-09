import socket


def check_domain_exists(domain):
    try:
        print(f"Checking DNS records for domain: {domain}")
        socket.gethostbyname(domain)
        return True
    except socket.error:
        print(f"Domain does not exist: {domain}")
        return False


def get_domain_ip(domain_name):  # Fetches the IP address of a given domain.
    try:
        ip_address = socket.gethostbyname(domain_name)
        return ip_address
    except socket.gaierror:
        print(f"Error resolving IP for {domain_name}: Host not found.")
        return "N/A"
    except Exception as e:
        print(f"Unexpected error resolving IP for {domain_name}: {e}")
        return "N/A"
