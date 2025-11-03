from fastapi import FastAPI, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_401_UNAUTHORIZED
import uvicorn
import os
from wol_service.auth import authenticate_user, create_access_token, require_user_from_cookie, \
    load_and_clear_login_data_from_envvar, get_user_from_cookie
from wol_service.wol import wake_on_lan
from wol_service.storage import ensure_parent_dir, load_hosts, save_hosts, Host
from typing import List

# Initialize FastAPI app
app = FastAPI(title="Wake on LAN Service")
templates = Jinja2Templates(directory="src/wol_service/templates")
security = HTTPBasic()

# Mount static files
app.mount("/static", StaticFiles(directory="src/wol_service/static"), name="static")

# In-memory storage for users
USERS = load_and_clear_login_data_from_envvar()
HOSTS_PATH = os.getenv("WOL_HOSTS_PATH", "hosts.json")

# Authentication middleware
def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    user = authenticate_user(USERS, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    if get_user_from_cookie(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def read_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(USERS, username, password)
    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("access_token", access_token, httponly=True)
    return response

@app.post("/wake")
async def wake_device(
    _ = Depends(require_user_from_cookie),
    mac_address: str = Form(...), 
    ip_address: str = Form("255.255.255.255"), 
    port_number: str = Form("9")
    ):
    try:
        wake_on_lan(mac_address, ip_address, port_number)
        return {"message": f"Magic packet sent to {mac_address}"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response


@app.on_event("startup")
def _startup():
    ensure_parent_dir(HOSTS_PATH)
    # If file missing, it’ll be created on first save

def get_hosts() -> List[Host]:
    return load_hosts(HOSTS_PATH)

def set_hosts(hosts: List[Host]) -> None:
    save_hosts(HOSTS_PATH, hosts)

@app.get("/api/hosts")
def list_hosts(user=Depends(require_user_from_cookie)):
    return get_hosts()

@app.post("/api/hosts")
def add_host(
    user=Depends(require_user_from_cookie),
    name: str = Form(...),
    mac: str = Form(...),
    ip: str = Form(...),
    port: int = Form(9),
):
    hosts = get_hosts()
    # optional: prevent dup by name or mac
    if any(h["name"] == name for h in hosts):
        raise HTTPException(400, "Host with this name already exists")
    hosts.append({"name": name.strip(), "mac": mac.strip(), "ip": ip.strip(), "port": int(port)})
    set_hosts(hosts)
    return {"ok": True}

@app.delete("/api/hosts")
def delete_host(user=Depends(require_user_from_cookie), name: str = Form(...)):
    hosts = [h for h in get_hosts() if h["name"] != name]
    set_hosts(hosts)
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=25644)
