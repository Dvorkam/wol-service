import os
from typing import Literal
import logging

logger = logging.getLogger("wol_service")

HOSTS_PATH = os.getenv("WOL_HOSTS_PATH", "hosts.json")
CONTAINER = os.getenv("CONTAINER", "false").lower() in ("1", "true", "yes", "on")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() in ("1", "true", "yes", "on")

_samesite_str = os.getenv("COOKIE_SAMESITE", "lax").lower()
if _samesite_str not in ("lax", "strict", "none"):
    logger.warning(
        "Invalid COOKIE_SAMESITE value '%s', defaulting to 'lax'. Must be one of: lax, strict, none.",
        _samesite_str,
    )
    _samesite_str = "lax"
COOKIE_SAMESITE: Literal["lax", "strict", "none"] = _samesite_str  # type: ignore
