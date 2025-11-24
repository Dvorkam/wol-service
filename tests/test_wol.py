import pytest
from wol_service.wol import wake_on_lan, validate_mac_address, create_magic_packet
from wol_service.wol import validate_ip_address, validate_port

def test_validate_mac_address_valid():
    """Test that valid MAC addresses are validated correctly"""
    valid_mac = "00:11:22:33:44:55"
    assert validate_mac_address(valid_mac) == True
    
    # Test without separators
    valid_mac_no_sep = "001122334455"
    assert validate_mac_address(valid_mac_no_sep) == True

@pytest.mark.parametrize("mac_address,validity", [
    ("00-11-22-33-44-55", True), # valid with dashes
    ("00:11:22:33:44:55", True), # valid with colons
    ("001122334455", True), # valid without separators
    ("0011.2233.4455", False), # invalid format
    ("00:11:22:33:44", False), # too short
    ("00:11:22:33:44:GG", False), # invalid hex characters
    ("", False) # empty string
])
def test_validate_mac_address(mac_address, validity):
    """Test that invalid MAC addresses are rejected"""
    assert validate_mac_address(mac_address) == validity


def test_wake_on_lan_functionality():
    """Test that wake_on_lan function can be called without errors"""
    # This test mainly ensures the function can be called
    # Actual network operations are not tested here due to complexity
    # Just verify the function exists and can be called
    # We don't actually send packets in tests
    assert callable(wake_on_lan)
    
def test_create_magic_packet():
    """Test that create_magic_packet generates correct magic packet"""
    mac_address = "00:11:22:33:44:55"
    answer = b'\xff\xff\xff\xff\xff\xff\x00\x11"3DU\x00\x11"3DU\x00\x11"3DU\x00\x11"3DU\x00\x11"3DU\x00\x11"3DU\x00\x11"3DU\x00\x11"3DU\x00\x11"3DU\x00\x11"3DU\x00\x11"3DU\x00\x11"3DU\x00\x11"3DU\x00\x11"3DU\x00\x11"3DU\x00\x11"3DU'
    packet = create_magic_packet(mac_address)
    assert isinstance(packet, bytes)
    assert answer == packet


def test_validate_ip_and_port():
    assert validate_ip_address("255.255.255.255") is True
    assert validate_ip_address("192.168.1.10") is True
    assert validate_ip_address("not-an-ip") is False
    assert validate_port(9) is True
    assert validate_port(0) is False
    assert validate_port(70000) is False
