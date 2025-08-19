import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from api.src.domain.auth.routers.auth import router as auth_router
from api.src.domain.users.routers.users import router as users_router
from api.src.domain.music.routers.youtube_download import router as music_router

from api.src.infrastructure.logger import configure_logger
from api.src.infrastructure.settings import settings


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
app.include_router(users_router)
app.include_router(music_router)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"SQLAlchemy Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "message": "Something went wrong! Developers has already been notified and will fix this asap!"
        },
    )


if __name__ == "__main__":
    uvicorn.run("main:app", port=settings.app.port, host=settings.app.host, reload=True)
