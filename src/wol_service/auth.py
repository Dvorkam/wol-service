import hashlib
import json
import os
import secrets
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple

from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from wol_service.storage import ensure_parent_dir


# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(32)
    print("Warning: SECRET_KEY was not set; generated a random key for this process. Tokens will not survive restarts.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
TOKEN_ISSUER = os.getenv("TOKEN_ISSUER", "wol-service")
TOKEN_AUDIENCE = os.getenv("TOKEN_AUDIENCE", "wol-service-users")
USERS_PATH = Path(os.getenv("USERS_PATH", "users.json"))
SECRET_FINGERPRINT = hashlib.sha256(SECRET_KEY.encode("utf-8")).hexdigest()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(users_db, username: str, password: str):
    user = users_db.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update(
        {
            "exp": expire,
            "iss": TOKEN_ISSUER,
            "aud": TOKEN_AUDIENCE,
        }
    )
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user_from_cookie(request: Request):
    try:
        return await require_user_from_cookie(request)
    except HTTPException:
        return None
    except JWTError:
        return None

async def require_user_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=TOKEN_AUDIENCE,
            issuer=TOKEN_ISSUER,
        )
        return payload.get("sub") or "anonymous"
    except JWTError:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def _atomic_write_json(path: Path, data) -> None:
    ensure_parent_dir(str(path))
    d = path.parent if path.parent != Path("") else Path(".")
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


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
        meta = {}
    else:
        users, meta = _load_users_from_file(USERS_PATH)
        stored_fp = meta.get("secret_fingerprint")
        if stored_fp and stored_fp != SECRET_FINGERPRINT:
            print("Warning: SECRET_KEY differs from the key used when users.json was written; existing sessions will be invalid.")
        env_users = _bootstrap_admin_from_env()
        # Merge env bootstrap without overwriting persisted users
        for username, user in env_users.items():
            if username == "__DISABLE__":
                continue
            users.setdefault(username, user)
        if env_users and "__DISABLE__" not in env_users and env_users:
            _atomic_write_json(
                USERS_PATH,
                {"users": users, "_meta": {"secret_fingerprint": SECRET_FINGERPRINT}},
            )
    _clear_admin_env()
    if not users:
        print("Warning: No users configured. Authentication is disabled; anyone can trigger wake/host actions.")
    return users


# Backwards-compatible alias
load_and_clear_login_data_from_envvar = load_users


def issue_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def validate_csrf(request: Request, submitted_token: str | None) -> None:
    cookie_token = request.cookies.get("csrf_token")
    if not cookie_token or not submitted_token or cookie_token != submitted_token:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid",
        )
