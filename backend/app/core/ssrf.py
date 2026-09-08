import ipaddress
import socket
from urllib.parse import urlparse

# Additional restricted CIDR blocks (e.g. AWS metadata 169.254.169.254, Carrier-Grade NAT 100.64.0.0/10)
ADDITIONAL_BLOCKED_NETWORKS = [
    ipaddress.ip_network("100.64.0.0/10"),      # Carrier-Grade NAT
    ipaddress.ip_network("169.254.0.0/16"),     # Link-Local / AWS IMDS
    ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),       # TEST-NET-1
    ipaddress.ip_network("198.51.100.0/24"),    # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),     # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),        # Multicast
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved
]


def validate_target_url(url: str) -> str:
    """Validate a target URL to prevent Server-Side Request Forgery (SSRF).
    
    Checks:
    1. Scheme restriction (only http and https are permitted).
    2. Missing or malformed hostnames.
    3. Blacklisted hostname strings (e.g. localhost, local domains).
    4. DNS resolution to ensure destination IP is not loopback, private, link-local, or restricted.
    
    Returns the normalized URL string if safe, or raises ValueError if unsafe.
    """
    if not url or not isinstance(url, str):
        raise ValueError("Target URL must be a non-empty string.")

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        # If user entered domain without scheme, prepend https://
        if "://" not in url:
            url = "https://" + url
        else:
            raise ValueError("Only HTTP and HTTPS protocols are allowed.")

    parsed = urlparse(url)
    hostname = parsed.hostname

    if not hostname:
        raise ValueError("Invalid target URL: missing hostname.")

    hostname_clean = hostname.lower().strip(".")

    # 1. String-level checks for common internal targets
    if hostname_clean == "localhost" or hostname_clean.endswith((".local", ".localhost", ".internal")):
        raise ValueError("Requests to local hostnames are forbidden for security reasons.")

    # 2. Try parsing hostname directly as IP address
    try:
        ip_obj = ipaddress.ip_address(hostname_clean)
        _check_ip_safety(ip_obj)
        return parsed.geturl()
    except ValueError as e:
        # Not a raw IP literal; proceed to DNS resolution
        if "does not appear to be an IPv4 or IPv6 address" not in str(e):
            raise e

    # 3. Resolve DNS safely
    try:
        addr_info = socket.getaddrinfo(hostname_clean, None)
    except socket.gaierror:
        raise ValueError(f"Could not resolve domain name: '{hostname}'")

    if not addr_info:
        raise ValueError(f"DNS resolution returned no records for domain: '{hostname}'")

    resolved_ips = set()
    for item in addr_info:
        ip_str = item[4][0]
        resolved_ips.add(ip_str)

    for ip_str in resolved_ips:
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            _check_ip_safety(ip_obj)
        except ValueError as e:
            raise ValueError(f"Domain '{hostname}' resolved to invalid or restricted IP '{ip_str}': {str(e)}")

    # Return normalized URL
    return parsed.geturl()


def _check_ip_safety(ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    """Helper function to verify whether an IP address is safe for outbound requests."""
    if ip_obj.is_loopback:
        raise ValueError(f"Loopback IP address ({ip_obj}) is forbidden.")
    if ip_obj.is_private:
        raise ValueError(f"Private network IP address ({ip_obj}) is forbidden.")
    if ip_obj.is_link_local:
        raise ValueError(f"Link-local IP address ({ip_obj}) is forbidden.")
    if ip_obj.is_multicast:
        raise ValueError(f"Multicast IP address ({ip_obj}) is forbidden.")
    if ip_obj.is_reserved:
        raise ValueError(f"Reserved IP address ({ip_obj}) is forbidden.")
    if ip_obj.is_unspecified:
        raise ValueError(f"Unspecified IP address ({ip_obj}) is forbidden.")

    # Check additional restricted CIDR blocks
    for network in ADDITIONAL_BLOCKED_NETWORKS:
        if ip_obj in network:
            raise ValueError(f"IP address ({ip_obj}) belongs to a restricted subnet ({network}).")
