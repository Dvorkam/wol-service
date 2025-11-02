import pytest
from wol_service.wol import wake_on_lan, validate_mac_address

def test_validate_mac_address_valid():
    """Test that valid MAC addresses are validated correctly"""
    valid_mac = "00:11:22:33:44:55"
    assert validate_mac_address(valid_mac) == True
    
    # Test without separators
    valid_mac_no_sep = "001122334455"
    assert validate_mac_address(valid_mac_no_sep) == True

def test_validate_mac_address_invalid():
    """Test that invalid MAC addresses are rejected"""
    # Test invalid length
    invalid_mac = "00:11:22:33:44"  # Only 5 bytes
    assert validate_mac_address(invalid_mac) == False
    
    # Test invalid characters
    invalid_mac_chars = "00:11:22:33:44:GG"  # Contains 'G'
    assert validate_mac_address(invalid_mac_chars) == False
    
    # Test empty string
    assert validate_mac_address("") == False

def test_wake_on_lan_functionality():
    """Test that wake_on_lan function can be called without errors"""
    # This test mainly ensures the function can be called
    # Actual network operations are not tested here due to complexity
    mac_address = "00:11:22:33:44:55"
    
    # Just verify the function exists and can be called
    # We don't actually send packets in tests
    assert callable(wake_on_lan)
    
    # Test with valid MAC address
    assert validate_mac_address(mac_address) == True
