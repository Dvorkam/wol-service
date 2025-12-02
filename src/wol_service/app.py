import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from wol_service.api import router as api_router
from wol_service.ui import router as ui_router
from wol_service.utils import ensure_parent_dir, get_resource_path
from wol_service.env import HOSTS_PATH, CONTAINER, LOG_LEVEL


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_parent_dir(HOSTS_PATH)
    # If file missing, it’ll be created on first save
    _warn_if_ephemeral_storage()
    yield


# Initialize FastAPI app
app = FastAPI(title="Wake on LAN Service", lifespan=lifespan)
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("wol_service")

# Mount static files
static_path = get_resource_path("wol_service", "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

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
