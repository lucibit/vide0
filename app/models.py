from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Video(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer)
    password = Column(String, nullable=True)
    share_token = Column(String, unique=True, index=True)
    transcoded = Column(Boolean, default=False)
    uploader_key_id = Column(String, nullable=True)

class ChunkUpload(Base):
    __tablename__ = 'chunk_uploads'
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(String, index=True)
    filename = Column(String)
    chunk_number = Column(Integer)
    total_chunks = Column(Integer)
    received = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    uploader_key_id = Column(String, nullable=True)

# Helper for DB setup
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = 'sqlite+aiosqlite:////nas/videos/db.sqlite3'

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 