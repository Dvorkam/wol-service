import logging
import os

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_401_UNAUTHORIZED

from wol_service.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_user_from_cookie,
    issue_csrf_token,
    require_user_from_cookie,
    validate_csrf,
)
from wol_service.user_management import load_users
from wol_service.validators import (
    validate_ip_address,
    validate_mac_address,
    validate_port,
)
from wol_service.wol import wake_on_lan
from wol_service.env import (
    COOKIE_SECURE,
    COOKIE_SAMESITE,
    CONTAINER,
)


router = APIRouter()
templates = Jinja2Templates(directory="src/wol_service/templates")
logger = logging.getLogger("wol_service")

# In-memory storage for users
USERS = load_users()
AUTH_ENABLED = bool(USERS)


def _enforce_csrf(request: Request, csrf_token: str | None) -> None:
    if not AUTH_ENABLED:
        return
    header_token = request.headers.get("X-CSRF-Token")
    submitted_token = csrf_token or header_token
    validate_csrf(request, submitted_token)


async def _require_user(request: Request):
    if not AUTH_ENABLED:
        return "anonymous"
    return await require_user_from_cookie(request)


async def _optional_user(request: Request):
    if not AUTH_ENABLED:
        return "anonymous"
    return await get_user_from_cookie(request)


def _warn_if_ephemeral_storage():
    if not CONTAINER:
        return
    if not os.path.ismount("/data"):
        logger.warning(
            "/data is not a mounted volume; users/hosts may be lost when the container stops."
        )
    else:
        logger.info(
            "\t/data is a mounted volume; users/hosts will persist across restarts."
        )


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    if AUTH_ENABLED and await _optional_user(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request=request, name="index.html")


@router.get("/login", response_class=HTMLResponse)
async def read_login(request: Request):
    if not AUTH_ENABLED:
        return RedirectResponse(url="/wake", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html")


@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if not AUTH_ENABLED:
        return RedirectResponse(url="/wake", status_code=303)
    user = authenticate_user(USERS, username, password)
    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    access_token = create_access_token(data={"sub": user["username"]})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        "csrf_token",
        issue_csrf_token(),
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


@router.get("/wake", response_class=HTMLResponse)
async def wake_page(request: Request):
    # Reuse the root handler so auth/no-auth logic stays consistent
    return await read_root(request)


@router.post("/wake")
async def wake_device(
    request: Request,
    _=Depends(_require_user),
    mac_address: str = Form(...),
    ip_address: str = Form("255.255.255.255"),
    port_number: str = Form("9"),
    csrf_token: str | None = Form(None),
):
    _enforce_csrf(request, csrf_token)
    if not validate_mac_address(mac_address):
        raise HTTPException(status_code=400, detail="Invalid MAC address format")
    if not validate_ip_address(ip_address):
        raise HTTPException(status_code=400, detail="Invalid IP/broadcast address")
    try:
        port_value = int(port_number)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Port must be an integer")
    if not validate_port(port_value):
        raise HTTPException(status_code=400, detail="Invalid port number")
    try:
        wake_on_lan(mac_address, ip_address, port_value)
        return {"message": f"Magic packet sent to {mac_address}"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    response.delete_cookie("csrf_token")
    return response
