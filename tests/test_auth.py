import importlib
import os

import pytest

import wol_service.auth as auth
from wol_service.auth import get_password_hash, load_users, verify_password


def test_password_hashing():
    password = "test_password"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_load_users_bootstraps_admin(tmp_path, monkeypatch):
    monkeypatch.setenv("USERS_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("ADMIN_USERNAME", "bootstrap_admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "bootstrap_password")
    importlib.reload(auth)
    users = load_users()
    assert "bootstrap_admin" in users
    assert verify_password("bootstrap_password", users["bootstrap_admin"]["hashed_password"]) is True
    # Ensure env cleared for security
    assert os.environ.get("ADMIN_USERNAME") is None
    assert os.environ.get("ADMIN_PASSWORD") is None


def test_missing_credentials_raise(monkeypatch, tmp_path):
    monkeypatch.setenv("USERS_PATH", str(tmp_path / "users.json"))
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    importlib.reload(auth)
    users = load_users()
    assert users == {}


def test_empty_env_disables_even_with_persisted_users(monkeypatch, tmp_path):
    # create persisted users
    users_path = tmp_path / "users.json"
    users_path.write_text('{"admin":{"username":"admin","hashed_password":"hash"}}', encoding="utf-8")
    monkeypatch.setenv("USERS_PATH", str(users_path))
    monkeypatch.setenv("ADMIN_USERNAME", "")
    monkeypatch.setenv("ADMIN_PASSWORD", "")
    importlib.reload(auth)
    users = load_users()
    assert users == {}
