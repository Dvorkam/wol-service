from typing import List

from fastapi import APIRouter, Depends, Form, HTTPException, Request

from wol_service.auth import require_user_from_cookie, validate_csrf
from wol_service.models import Host
from wol_service.storage import load_hosts, save_hosts
from wol_service.validators import (
    validate_ip_address,
    validate_mac_address,
    validate_port,
)
from wol_service.env import HOSTS_PATH


router = APIRouter()


def get_hosts() -> List[Host]:
    return load_hosts(HOSTS_PATH)


def set_hosts(hosts: List[Host]) -> None:
    save_hosts(HOSTS_PATH, hosts)


@router.get("/api/hosts")
def list_hosts(user=Depends(require_user_from_cookie)):
    return get_hosts()


@router.post("/api/hosts")
async def add_host(
    request: Request,
    user=Depends(require_user_from_cookie),
    name: str = Form(...),
    mac: str = Form(...),
    ip: str = Form(...),
    port: int = Form(9),
    csrf_token: str | None = Form(None),
):
    validate_csrf(request, csrf_token)
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
    hosts.append(
        {"name": name.strip(), "mac": mac.strip(), "ip": ip.strip(), "port": int(port)}
    )
    set_hosts(hosts)
    return {"ok": True}


@router.delete("/api/hosts")
async def delete_host(
    request: Request,
    user=Depends(require_user_from_cookie),
    name: str = Form(...),
    csrf_token: str | None = Form(None),
):
    validate_csrf(request, csrf_token)
    if not name.strip():
        raise HTTPException(400, "Host name is required")
    hosts = [h for h in get_hosts() if h["name"] != name]
    set_hosts(hosts)
    return {"ok": True}
