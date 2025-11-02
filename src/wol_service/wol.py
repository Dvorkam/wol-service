import socket

def wake_on_lan(mac_address:str, ip_address="255.255.255.255", port=9):
    """
    Wake up a device using Wake on LAN.
    
    Args:
        mac_address (str): MAC address of the device to wake (format: "00:11:22:33:44:55")
        ip_address (str): Broadcast address (default: "255.255.255.255")
        port (int): Port to send the magic packet (default: 9)
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    # Remove any separators (colons, dashes, etc.) from MAC address
    mac_address = mac_address.replace(':', '').replace('-', '')
    
    # Convert MAC address to bytes
    mac_bytes = bytes.fromhex(mac_address)
    
    # Create magic packet
    # First 6 bytes are 0xFF
    # Next 16 repetitions of the MAC address
    magic_packet = b'\xff' * 6 + mac_bytes * 16
    
    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    try:
        # Send magic packet
        sock.sendto(magic_packet, (ip_address, port))
        return True
    except Exception as e:
        raise Exception(f"Failed to send magic packet: {str(e)}")
    finally:
        sock.close()

def validate_mac_address(mac_address):
    """
    Validate MAC address format.
    
    Args:
        mac_address (str): MAC address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Remove any separators
    mac_address = mac_address.replace(':', '').replace('-', '')
    
    # Check if it's a valid MAC address (12 hexadecimal characters)
    if len(mac_address) != 12:
        return False
    
    try:
        int(mac_address, 16)
        return True
    except ValueError:
        return False
