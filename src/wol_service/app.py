import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from wol_service.api import router as api_router
from wol_service.ui import router as ui_router
from wol_service.utils import ensure_parent_dir
from wol_service.env import HOSTS_PATH, CONTAINER


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_parent_dir(HOSTS_PATH)
    # If file missing, it’ll be created on first save
    _warn_if_ephemeral_storage()
    yield


# Initialize FastAPI app
app = FastAPI(title="Wake on LAN Service", lifespan=lifespan)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("wol_service")

# Mount static files
app.mount("/static", StaticFiles(directory="src/wol_service/static"), name="static")

# Include routers
app.include_router(api_router)
app.include_router(ui_router)

# In-memory storage for users


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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=25644)
