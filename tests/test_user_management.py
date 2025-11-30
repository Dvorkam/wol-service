import hashlib
import json
import importlib
import os


import wol_service.user_management as um
from wol_service.auth import verify_password


def test_load_users_bootstraps_admin(tmp_path, monkeypatch):
    monkeypatch.setenv("USERS_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("ADMIN_USERNAME", "bootstrap_admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "bootstrap_password")
    importlib.reload(um)
    users = um.load_users()
    assert "bootstrap_admin" in users
    assert (
        verify_password(
            "bootstrap_password", users["bootstrap_admin"]["hashed_password"]
        )
        is True
    )
    # Ensure env cleared for security
    assert os.environ.get("ADMIN_USERNAME") is None
    assert os.environ.get("ADMIN_PASSWORD") is None
    # Ensure fingerprint saved
    payload = (tmp_path / "users.json").read_text(encoding="utf-8")
    assert um.SECRET_FINGERPRINT in payload


def test_missing_credentials_raise(monkeypatch, tmp_path):
    monkeypatch.setenv("USERS_PATH", str(tmp_path / "users.json"))
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    importlib.reload(um)
    users = um.load_users()
    assert users == {}


def test_empty_env_disables_even_with_persisted_users(monkeypatch, tmp_path):
    # create persisted users
    users_path = tmp_path / "users.json"
    users_path.write_text(
        '{"admin":{"username":"admin","hashed_password":"hash"}}', encoding="utf-8"
    )
    monkeypatch.setenv("USERS_PATH", str(users_path))
    monkeypatch.setenv("ADMIN_USERNAME", "")
    monkeypatch.setenv("ADMIN_PASSWORD", "")
    importlib.reload(um)
    users = um.load_users()
    assert users == {}


def test_secret_mismatch_warns(monkeypatch, tmp_path, capsys):
    users_path = tmp_path / "users.json"
    original_fp = hashlib.sha256(b"oldsecret").hexdigest()
    users_path.write_text(
        json.dumps(
            {
                "users": {"user": {"username": "user", "hashed_password": "hash"}},
                "_meta": {"secret_fingerprint": original_fp},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("USERS_PATH", str(users_path))
    monkeypatch.setenv("SECRET_KEY", "newsecret")
    importlib.reload(um)
    um.load_users()
    captured = capsys.readouterr()
    assert "SECRET_KEY differs" in captured.out
