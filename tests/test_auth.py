from wol_service.auth import get_password_hash, verify_password


def test_password_hashing():
    password = "test_password"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False
