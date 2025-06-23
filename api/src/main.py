import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from api.src.auth.routers import router as auth_router
from utils.logger import configure_logger
from config import settings


configure_logger()
logger = logging.getLogger("my_app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("App started!")
    yield
    logger.info("App stopped!")


app = FastAPI(
    title="Music app API",
    version="0.1.0",
    root_path="/api/v1",
    debug=True,
    lifespan=lifespan,
)

app.include_router(auth_router)


if __name__ == "__main__":
    uvicorn.run("main:app", port=settings.APP_PORT, host=settings.APP_HOST, reload=True)
