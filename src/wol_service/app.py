import os
from typing import List

import uvicorn
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_401_UNAUTHORIZED

from wol_service.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    USERS_PATH,
    authenticate_user,
    create_access_token,
    get_user_from_cookie,
    issue_csrf_token,
    load_users,
    require_user_from_cookie,
    validate_csrf,
)
from wol_service.storage import Host, ensure_parent_dir, load_hosts, save_hosts
from wol_service.wol import validate_ip_address, validate_mac_address, validate_port, wake_on_lan

# Initialize FastAPI app
app = FastAPI(title="Wake on LAN Service")
templates = Jinja2Templates(directory="src/wol_service/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="src/wol_service/static"), name="static")

# In-memory storage for users
USERS = load_users()
AUTH_ENABLED = bool(USERS)
HOSTS_PATH = os.getenv("WOL_HOSTS_PATH", "hosts.json")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() in ("1", "true", "yes", "on")
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")


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
    if not os.path.exists("/.dockerenv"):
        return
    if not os.path.ismount("/data"):
        print("Warning: /data is not a mounted volume; users/hosts may be lost when the container stops.")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    if AUTH_ENABLED and await _optional_user(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def read_login(request: Request):
    if not AUTH_ENABLED:
        return RedirectResponse(url="/wake", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
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


@app.get("/wake", response_class=HTMLResponse)
async def wake_page(request: Request):
    # Reuse the root handler so auth/no-auth logic stays consistent
    return await read_root(request)


@app.post("/wake")
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


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    response.delete_cookie("csrf_token")
    return response


@app.on_event("startup")
def _startup():
    ensure_parent_dir(HOSTS_PATH)
    # If file missing, it’ll be created on first save
    _warn_if_ephemeral_storage()


def get_hosts() -> List[Host]:
    return load_hosts(HOSTS_PATH)


def set_hosts(hosts: List[Host]) -> None:
    save_hosts(HOSTS_PATH, hosts)


@app.get("/api/hosts")
def list_hosts(user=Depends(_require_user)):
    return get_hosts()


@app.post("/api/hosts")
async def add_host(
    request: Request,
    user=Depends(_require_user),
    name: str = Form(...),
    mac: str = Form(...),
    ip: str = Form(...),
    port: int = Form(9),
    csrf_token: str | None = Form(None),
):
    _enforce_csrf(request, csrf_token)
    if not name.strip():
        raise HTTPException(400, "Host name is required")
    if not validate_mac_address(mac):
        raise HTTPException(400, "Invalid MAC address format")
    if not validate_ip_address(ip):
        raise HTTPException(400, "Invalid IP/broadcast address")
    if not validate_port(port):
        raise HTTPException(400, "Invalid port number")
    hosts = get_hosts()
    if any(h["name"] == name for h in hosts):
        raise HTTPException(400, "Host with this name already exists")
    if any(h["mac"].lower() == mac.strip().lower() for h in hosts):
        raise HTTPException(400, "Host with this MAC already exists")
    hosts.append({"name": name.strip(), "mac": mac.strip(), "ip": ip.strip(), "port": int(port)})
    set_hosts(hosts)
    return {"ok": True}


@app.delete("/api/hosts")
async def delete_host(
    request: Request,
    user=Depends(_require_user),
    name: str = Form(...),
    csrf_token: str | None = Form(None),
):
    _enforce_csrf(request, csrf_token)
    if not name.strip():
        raise HTTPException(400, "Host name is required")
    hosts = [h for h in get_hosts() if h["name"] != name]
    set_hosts(hosts)
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=25644)
