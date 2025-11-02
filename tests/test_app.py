import pytest
from wol_service.app import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_read_root():
    """Test the main page can be accessed"""
    response = client.get("/")
    assert response.status_code == 200

def test_read_login():
    """Test the login page can be accessed"""
    response = client.get("/login")
    assert response.status_code == 200

def test_wake_endpoint_exists():
    """Test that the wake endpoint exists"""
    # Test with minimal required data
    response = client.post("/wake", data={"mac_address": "00:11:22:33:44:55"})
    assert response.status_code == 200

def test_app_structure():
    """Test that the app has the expected structure"""
    assert app.title == "Wake on LAN Service"
    assert hasattr(app, "routes")

if __name__ == "__main__":
    test_wake_endpoint_exists()
