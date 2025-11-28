import ipaddress
import re


def validate_mac_address(mac_address) -> bool:
    """
    Validate MAC address format.
    
    Args:
        mac_address (str): MAC address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    valid_mac_address= re.compile(r'^([0-9A-Fa-f]{2}([-:]?)){5}([0-9A-Fa-f]{2})$|^([0-9A-Fa-f]{12})$')
    return bool(valid_mac_address.match(mac_address))

def validate_ip_address(value: str) -> bool:
    """Allow IPv4 unicast or broadcast addresses."""
    try:
        ip = ipaddress.ip_address(value)
        # Broadcast is not directly detected by ip_address, so allow IPv4 all-ones
        if ip.version == 4:
            return True
        return False
    except ValueError:
        # Also permit dotted broadcast like 255.255.255.255
        if value == "255.255.255.255":
            return True
        return False

def validate_port(port: int) -> bool:
    try:
        port = int(port)
    except (TypeError, ValueError):
        return False
    return 1 <= port <= 65535
