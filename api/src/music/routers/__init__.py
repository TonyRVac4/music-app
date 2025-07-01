from fastapi import APIRouter

from .youtube_download import router as yt_router

router = APIRouter()
router.include_router(yt_router)
