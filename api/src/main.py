from fastapi import FastAPI
import uvicorn

from auth.router import router as auth_router
from config import settings

app = FastAPI(
    title="Music app API",
    version="0.1.0",
    root_path="/api/v1",
    debug=True,
)

app.include_router(auth_router)


if __name__ == "__main__":
    uvicorn.run("main:app", port=settings.APP_PORT, host=settings.APP_HOST, reload=True)
