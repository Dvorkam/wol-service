from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Request
from starlette.status import HTTP_401_UNAUTHORIZED
import os


# Password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_from_cookie(request: Request):
    try:
        return require_user_from_cookie(request)
    except HTTPException:
        return None
    except JWTError:
        return None

def require_user_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub") or "anonymous"
    except JWTError:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Add default admin account from environment variables during app start
def load_and_clear_login_data_from_envvar() -> dict:
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    users = {}
    
    if admin_username and admin_password:
        from wol_service.auth import get_password_hash
        users[admin_username] = {
            "username": admin_username,
            "hashed_password": get_password_hash(admin_password)
        }
        print(f"Default admin user '{admin_username}' created successfully")
    else:
        print("Warning: No default admin created. Service will run without authentication requirements.")
    os.environ.pop("ADMIN_PASSWORD", None)  # Remove password from environment for security
    os.environ.pop("ADMIN_USERNAME", None)  # Remove username from environment for security
    return users
