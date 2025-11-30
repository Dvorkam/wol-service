import pytest
from wol_service.validators import (
    validate_mac_address,
    validate_ip_address,
    validate_port,
)


def test_validate_mac_address_valid():
    """Test that valid MAC addresses are validated correctly"""
    valid_mac = "00:11:22:33:44:55"
    assert validate_mac_address(valid_mac)

    # Test without separators
    valid_mac_no_sep = "001122334455"
    assert validate_mac_address(valid_mac_no_sep)


@pytest.mark.parametrize(
    "mac_address,validity",
    [
        ("00-11-22-33-44-55", True),  # valid with dashes
        ("00:11:22:33:44:55", True),  # valid with colons
        ("001122334455", True),  # valid without separators
        ("0011.2233.4455", False),  # invalid format
        ("00:11:22:33:44", False),  # too short
        ("00:11:22:33:44:GG", False),  # invalid hex characters
        ("", False),  # empty string
    ],
)
def test_validate_mac_address(mac_address, validity):
    """Test that invalid MAC addresses are rejected"""
    assert validate_mac_address(mac_address) == validity


def test_validate_ip_and_port():
    assert validate_ip_address("255.255.255.255") is True
    assert validate_ip_address("192.168.1.10") is True
    assert validate_ip_address("not-an-ip") is False
    assert validate_port(9) is True
    assert validate_port(0) is False
    assert validate_port(70000) is False
