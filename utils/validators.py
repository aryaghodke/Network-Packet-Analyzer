"""
Input validation helpers used by the filter panel and other GUI forms.
"""

import ipaddress


def is_valid_ip(value: str) -> bool:
    """Return True if `value` is a complete, valid IPv4/IPv6 address."""
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def is_valid_ip_or_partial(value: str) -> bool:
    """
    The IP filter in this application works as a substring match (e.g.
    typing "192.168" should be accepted, even though it is not a full
    address). This validator simply rejects characters that could never
    appear in a legitimate IPv4/IPv6 address or fragment thereof.
    """
    if not value:
        return True
    allowed_chars = set("0123456789abcdefABCDEF.:")
    return all(c in allowed_chars for c in value)


def is_valid_port(value: str) -> bool:
    """Return True if `value` is empty (no filter) or a valid port number."""
    if not value:
        return True
    if not value.isdigit():
        return False
    port = int(value)
    return 0 <= port <= 65535
