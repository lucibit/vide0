from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.config import Config, get_config
from app.models import AsyncSessionLocal, Video
import os

# Path where NAS is mounted inside the container
NAS_MOUNT_PATH = "/nas/videos"
VIDEOS_DIR = os.path.join(NAS_MOUNT_PATH, "videos")

# Templates directory
templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/play/{share_token}", response_class=HTMLResponse)
async def play_video(request: Request, share_token: str, db: AsyncSession = Depends(get_db), config: Config = Depends(get_config)):
    # Find video by share token
    result = await db.execute(
        select(Video).where(Video.share_token == share_token)
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check if file exists
    video_path = os.path.join(VIDEOS_DIR, video.filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    # Generate video URL for the player
    video_url = f"/videos/{share_token}"
    
    return templates.TemplateResponse(
        "video_player.html",
        {
            "request": request,
            "video_url": video_url,
            "filename": video.filename,
            "upload_date": video.upload_date.strftime("%Y-%m-%d %H:%M:%S") if video.upload_date else "Unknown",
            "file_size": f"{video.file_size / (1024*1024):.1f} MB" if video.file_size else "Unknown",
            "share_token": share_token,
            "domain": config.domain,
        }
    ) 