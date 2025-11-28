import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Tuple

from wol_service.auth import get_password_hash
from wol_service.utils import atomic_write

USERS_PATH = Path(os.getenv("USERS_PATH", "users.json"))
SECRET_KEY = os.getenv("SECRET_KEY")
SECRET_FINGERPRINT = hashlib.sha256(SECRET_KEY.encode("utf-8")).hexdigest() if SECRET_KEY else None


def _load_users_from_file(path: Path) -> Tuple[Dict[str, dict], Dict[str, str]]:
    if not path.exists():
        return {}, {}
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    meta = {}
    if isinstance(payload, dict):
        meta = payload.get("_meta") or {}
        if "users" in payload:
            payload = payload["users"]
    if isinstance(payload, dict):
        return payload, meta
    if isinstance(payload, list):
        return {u["username"]: u for u in payload if isinstance(u, dict) and "username" in u}, meta
    return {}, meta


def _bootstrap_admin_from_env() -> Dict[str, dict]:
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_username == "" and admin_password == "":
        return {"__DISABLE__": {}}
    if admin_username and admin_password:
        return {
            admin_username: {
                "username": admin_username,
                "hashed_password": get_password_hash(admin_password),
            }
        }
    if admin_username or admin_password:
        raise RuntimeError("Both ADMIN_USERNAME and ADMIN_PASSWORD must be provided to create the default admin.")
    return {}


def _clear_admin_env() -> None:
    os.environ.pop("ADMIN_PASSWORD", None)
    os.environ.pop("ADMIN_USERNAME", None)


def load_users() -> Dict[str, dict]:
    disable_flag = os.getenv("ADMIN_USERNAME") == "" and os.getenv("ADMIN_PASSWORD") == ""
    if disable_flag:
        users = {}
    else:
        users, meta = _load_users_from_file(USERS_PATH)
        if SECRET_FINGERPRINT:
            stored_fp = meta.get("secret_fingerprint")
            if stored_fp and stored_fp != SECRET_FINGERPRINT:
                print("Warning: SECRET_KEY differs from the key used when users.json was written; existing sessions will be invalid.")
        env_users = _bootstrap_admin_from_env()
        # Merge env bootstrap without overwriting persisted users
        for username, user in env_users.items():
            if username == "__DISABLE__":
                continue
            users.setdefault(username, user)
        if env_users and "__DISABLE__" not in env_users:
            atomic_write(
                USERS_PATH,
                {"users": users, "_meta": {"secret_fingerprint": SECRET_FINGERPRINT}},
            )
    _clear_admin_env()
    if not users:
        print("Warning: No users configured. Authentication is disabled; anyone can trigger wake/host actions.")
    return users


# Backwards-compatible alias
load_and_clear_login_data_from_envvar = load_users
