import asyncio

import httpx

from wol_service import app

ADMIN_USER = "test_admin"
ADMIN_PASS = "test_password"


async def login_and_get_csrf(client: httpx.AsyncClient):
    resp = await client.post("/login", data={"username": ADMIN_USER, "password": ADMIN_PASS}, follow_redirects=False)
    assert resp.status_code == 303
    return client.cookies.get("csrf_token")


def test_add_host_validates_input():
    async def _run():
        transport = httpx.ASGITransport(app=app.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            csrf_token = await login_and_get_csrf(client)
            response = await client.post(
                "/api/hosts",
                data={"name": "bad", "mac": "ZZ:ZZ:ZZ:ZZ:ZZ:ZZ", "ip": "not-an-ip", "port": 9, "csrf_token": csrf_token},
            )
            assert response.status_code == 400
    asyncio.run(_run())
