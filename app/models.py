from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Video(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    upload_date = Column(DateTime, default=datetime.now())
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
    created_at = Column(DateTime, default=datetime.now())
    uploader_key_id = Column(String, nullable=True)

class PublicKey(Base):
    __tablename__ = 'public_keys'
    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String, unique=True, index=True)
    public_key_pem = Column(Text, nullable=False)  # Changed to Text for longer PEM keys
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now())
    created_by = Column(String, nullable=True)  # key_id of who created this key
    domain = Column(String, nullable=True)  # Domain this key was created for

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