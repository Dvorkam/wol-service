import asyncio
import importlib

import httpx

from wol_service import app, ui

ADMIN_USER = "test_admin"
ADMIN_PASS = "test_password"


async def login_and_get_csrf(client: httpx.AsyncClient):
    resp = await client.post("/login", data={"username": ADMIN_USER, "password": ADMIN_PASS}, follow_redirects=False)
    assert resp.status_code == 303
    return client.cookies.get("csrf_token")


def test_root_requires_auth():
    async def _run():
        transport = httpx.ASGITransport(app=app.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/", follow_redirects=False)
            assert response.status_code == 303
            assert response.headers["location"] == "/login"
    asyncio.run(_run())


def test_login_sets_cookies():
    async def _run():
        transport = httpx.ASGITransport(app=app.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            csrf_token = await login_and_get_csrf(client)
            assert csrf_token
            assert client.cookies.get("access_token")
    asyncio.run(_run())


def test_wake_requires_csrf(monkeypatch):
    async def _run():
        transport = httpx.ASGITransport(app=app.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            await login_and_get_csrf(client)
            monkeypatch.setattr("wol_service.wol.wake_on_lan", lambda *args, **kwargs: True)
            response = await client.post(
                "/wake",
                data={"mac_address": "00:11:22:33:44:55", "ip_address": "255.255.255.255", "port_number": "9"},
                follow_redirects=False,
            )
            assert response.status_code == 403
    asyncio.run(_run())


def test_wake_with_csrf(monkeypatch):
    async def _run():
        transport = httpx.ASGITransport(app=app.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            csrf_token = await login_and_get_csrf(client)
            monkeypatch.setattr("wol_service.wol.wake_on_lan", lambda *args, **kwargs: True)
            response = await client.post(
                "/wake",
                data={
                    "mac_address": "00:11:22:33:44:55",
                    "ip_address": "255.255.255.255",
                    "port_number": "9",
                    "csrf_token": csrf_token,
                },
            )
            assert response.status_code == 200
            assert "message" in response.json()
    asyncio.run(_run())


def test_no_auth_allows_direct_access(tmp_path, monkeypatch):
    import wol_service.user_management as um
    
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.setenv("SECRET_KEY", "no-auth-secret")
    monkeypatch.setenv("USERS_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("WOL_HOSTS_PATH", str(tmp_path / "hosts.json"))

    importlib.reload(um)
    app_mod = importlib.reload(app)
    ui_mod = importlib.reload(ui)
    
    monkeypatch.setattr(ui_mod, "wake_on_lan", lambda *args, **kwargs: True)

    async def _run():
        transport = httpx.ASGITransport(app=app_mod.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/login", follow_redirects=False)
            assert resp.status_code == 303
            assert resp.headers["location"] == "/wake"
            resp = await client.get("/wake", follow_redirects=False)
            assert resp.status_code == 200
            resp = await client.get("/", follow_redirects=False)
            assert resp.status_code == 200
            resp = await client.post(
                "/wake",
                data={"mac_address": "00:11:22:33:44:55", "ip_address": "255.255.255.255", "port_number": "9"},
            )
            assert resp.status_code == 200

    asyncio.run(_run())

    # restore default app state for later tests
    monkeypatch.setenv("ADMIN_USERNAME", ADMIN_USER)
    monkeypatch.setenv("ADMIN_PASSWORD", ADMIN_PASS)
    importlib.reload(um)
    importlib.reload(app)


def test_warn_if_data_not_mounted(monkeypatch, caplog):
    monkeypatch.setenv("WOL_HOSTS_PATH", "/data/hosts.json")
    monkeypatch.setenv("USERS_PATH", "/data/users.json")
    
    app_mod = importlib.reload(app)

    monkeypatch.setattr(app_mod, "CONTAINER", True)
    monkeypatch.setattr(app_mod.os.path, "ismount", lambda p: False)
    caplog.set_level("WARNING")
    app_mod._warn_if_ephemeral_storage()
    assert any("not a mounted volume" in rec.message for rec in caplog.records)
