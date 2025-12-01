import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from wol_service.env import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM,
    TOKEN_AUDIENCE,
    TOKEN_ISSUER,
)


# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT settings
if not SECRET_KEY:
    SECRET_KEY = str(secrets.token_urlsafe(32))
    print(
        "Warning: SECRET_KEY was not set; generated a random key for this process. Tokens will not survive restarts."
    )


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
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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


def issue_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def validate_csrf(request: Request, submitted_token: str | None) -> None:
    cookie_token = request.cookies.get("csrf_token")
    if not cookie_token or not submitted_token or cookie_token != submitted_token:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid",
        )
