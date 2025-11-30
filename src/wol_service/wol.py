import socket

from wol_service.validators import (
    validate_ip_address,
    validate_mac_address,
    validate_port,
)


def wake_on_lan(mac_address: str, ip_address: str, port: int = 9):
    """
    Wake up a device using Wake on LAN.

    Args:
        mac_address (str): MAC address of the device to wake (format: "00:11:22:33:44:55")
        ip_address (str): IP address to send the magic packet to
        port (int): Port to send the magic packet (default: 9)

    Returns:
        bool: True if successful, False otherwise
    """

    if not validate_mac_address(mac_address):
        raise ValueError("Invalid MAC address format")
    if not validate_ip_address(ip_address):
        raise ValueError("Invalid IP address or broadcast address")
    port = int(port)
    if not validate_port(port):
        raise ValueError("Invalid port number")

    magic_packet = create_magic_packet(mac_address)

    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    try:
        # Send magic packet
        sock.sendto(magic_packet, (ip_address, int(port)))
        return True
    except Exception as e:
        raise Exception(f"Failed to send magic packet: {str(e)}")
    finally:
        sock.close()


def create_magic_packet(valid_mac_address: str) -> bytes:
    """
    Create a magic packet for Wake on LAN.

    Args:
        mac_address (str): MAC address of the device to wake (format: "00:11:22:33:44:55")

    Returns:
        bytes: The magic packet
    """
    # Remove any separators from MAC address
    valid_mac_address = valid_mac_address.replace(":", "").replace("-", "")

    # Convert MAC address to bytes
    mac_bytes = bytes.fromhex(valid_mac_address)

    # Create magic packet
    magic_packet = b"\xff" * 6 + mac_bytes * 16
    return magic_packet
