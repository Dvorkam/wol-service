from fastapi import FastAPI, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_401_UNAUTHORIZED
import uvicorn
import os
from .auth import authenticate_user, create_access_token, verify_password
from .wol import wake_on_lan

# Initialize FastAPI app
app = FastAPI(title="Wake on LAN Service")
templates = Jinja2Templates(directory="src/wol_service/templates")
security = HTTPBasic()

# Mount static files
app.mount("/static", StaticFiles(directory="src/wol_service/static"), name="static")

# In-memory storage for users (in production, use a proper database)
USERS = {
    "admin": {
        "username": "admin",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$..."
    }
}

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
async def wake_device(mac_address: str = Form(...), ip_address: str = Form("255.255.255.255"), port_number: str = Form("9")):
    if ip := os.environ.get("WOL_BROADCAST_IP"):
        ip_address = ip
    if port:= os.environ.get("WOL_PORT"):
        port_number = int(port)
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=25644)
