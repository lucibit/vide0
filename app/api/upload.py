from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import AsyncSessionLocal, ChunkUpload, Video
from app.core.security import require_signature
import uuid
import os
import shutil
from datetime import datetime


# Path where NAS is mounted inside the container
NAS_MOUNT_PATH = "/nas/videos"
CHUNKS_DIR = os.path.join(NAS_MOUNT_PATH, "chunks")
VIDEOS_DIR = os.path.join(NAS_MOUNT_PATH, "videos")
os.makedirs(CHUNKS_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename to prevent overwrites"""
    name, ext = os.path.splitext(original_filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{name}_{timestamp}_{unique_id}{ext}"        

@router.post("/upload/initiate")
async def initiate_upload(
    filename: str = Form(...),
    total_chunks: int = Form(...),
    db: AsyncSession = Depends(get_db),
    key_id: str = Depends(require_signature)
):
    upload_id = str(uuid.uuid4())
    # Generate unique filename to prevent overwrites
    unique_filename = generate_unique_filename(filename)
    
    # Store initial chunk upload session in DB
    for chunk_number in range(1, total_chunks + 1):
        chunk = ChunkUpload(
            upload_id=upload_id,
            filename=unique_filename,  # Use unique filename
            chunk_number=chunk_number,
            total_chunks=total_chunks,
            received=False,
            created_at=datetime.utcnow(),
            uploader_key_id=key_id  # Store uploader's key_id
        )
        db.add(chunk)
    await db.commit()
    return {"upload_id": upload_id}

@router.post("/upload/chunk")
async def upload_chunk(
    upload_id: str = Form(...),
    chunk_number: int = Form(...),
    total_chunks: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    key_id: str = Depends(require_signature)
):
    # Enforce key_id consistency
    result = await db.execute(
        select(ChunkUpload).where(
            ChunkUpload.upload_id == upload_id,
            ChunkUpload.chunk_number == chunk_number
        )
    )
    chunk = result.scalar_one_or_none()
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk upload session not found")
    if chunk.uploader_key_id != key_id:
        raise HTTPException(status_code=403, detail="Uploader key_id mismatch for this upload_id")
    # Save chunk to disk using shutil
    chunk_path = os.path.join(CHUNKS_DIR, f"{upload_id}_{chunk_number}.part")
    with open(chunk_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    chunk.received = True
    await db.commit()
    return {"status": "chunk received"}

@router.post("/upload/complete")
async def complete_upload(
    upload_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
    key_id: str = Depends(require_signature)
):
    # Get all chunks for this upload
    result = await db.execute(
        select(ChunkUpload).where(ChunkUpload.upload_id == upload_id)
    )
    chunks = result.scalars().all()
    if not chunks:
        raise HTTPException(status_code=404, detail="No chunks found for this upload_id")
    # Enforce key_id consistency
    if any(chunk.uploader_key_id != key_id for chunk in chunks):
        raise HTTPException(status_code=403, detail="Uploader key_id mismatch for this upload_id")
    # Ensure all chunks are received
    if not all(chunk.received for chunk in chunks):
        raise HTTPException(status_code=400, detail="Not all chunks uploaded yet")
    unique_filename = chunks[0].filename  # This is now the unique filename
    total_chunks = chunks[0].total_chunks
    assembled_path = os.path.join(VIDEOS_DIR, unique_filename)
    # Assemble chunks using shutil
    with open(assembled_path, "wb") as outfile:
        for i in range(1, total_chunks + 1):
            chunk_path = os.path.join(CHUNKS_DIR, f"{upload_id}_{i}.part")
            with open(chunk_path, "rb") as infile:
                shutil.copyfileobj(infile, outfile)
            os.remove(chunk_path)
    # Store video metadata in DB
    file_size = os.path.getsize(assembled_path)
    share_token = str(uuid.uuid4())
    video = Video(
        filename=unique_filename,  # Store the unique filename
        upload_date=datetime.utcnow(),
        file_size=file_size,
        share_token=share_token,
        transcoded=False,
        uploader_key_id=key_id  # Store uploader's key_id
    )
    db.add(video)
    # Clean up chunk records
    for chunk in chunks:
        await db.delete(chunk)
    await db.commit()
    return {"status": "upload complete", "video_link": f"/videos/{share_token}"}

@router.get("/videos/{share_token}")
async def share_video(share_token: str, db: AsyncSession = Depends(get_db)):
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
    
    # Return the video file
    return FileResponse(
        path=video_path,
        filename=video.filename,
        media_type="video/mp4"  # You might want to detect this dynamically
    ) 