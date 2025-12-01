import os
from typing import Literal
import logging

logger = logging.getLogger("wol_service")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
ALGORITHM = "HS256"
CONTAINER = os.getenv("CONTAINER", "false").lower() in ("1", "true", "yes", "on")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() in (
    "1",
    "true",
    "yes",
    "on",
)
HOSTS_PATH = os.getenv("WOL_HOSTS_PATH", "hosts.json")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
TOKEN_ISSUER = os.getenv("TOKEN_ISSUER", "wol-service")
TOKEN_AUDIENCE = os.getenv("TOKEN_AUDIENCE", "wol-service-users")
SECRET_KEY = str(os.getenv("SECRET_KEY"))

_samesite_str = os.getenv("COOKIE_SAMESITE", "lax").lower()
if _samesite_str not in ("lax", "strict", "none"):
    logger.warning(
        "Invalid COOKIE_SAMESITE value '%s', defaulting to 'lax'. Must be one of: lax, strict, none.",
        _samesite_str,
    )
    _samesite_str = "lax"
COOKIE_SAMESITE: Literal["lax", "strict", "none"] = _samesite_str  # type: ignore
