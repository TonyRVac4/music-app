import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from sqlalchemy.exc import SQLAlchemyError

from api.src.users.routers import router as auth_router
from api.src.music.routers import router as music_router

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
app.include_router(music_router)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"message": f"Something went wrong! Developers has already been notified and will fix this asap!"}
    )


if __name__ == "__main__":
    uvicorn.run("main:app", port=settings.APP_PORT, host=settings.APP_HOST, reload=True)
