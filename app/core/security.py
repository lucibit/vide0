import base64
import os
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import AsyncSessionLocal, PublicKey
from app.core.config import config

from fastapi import HTTPException, Header, Depends, Request

# Database helper functions
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_public_key_by_id(session: AsyncSession, key_id: str) -> PublicKey:
    """Get a public key by key_id from the database"""
    result = await session.execute(
        select(PublicKey).where(PublicKey.key_id == key_id)
    )
    return result.scalar_one_or_none()

async def add_public_key_to_db(
    session: AsyncSession, 
    key_id: str, 
    public_key_pem: str, 
    is_admin: bool = False,
    created_by: str = None,
    domain: str = None
) -> PublicKey:
    """Add a public key to the database"""
    # Check if key already exists
    existing_key = await get_public_key_by_id(session, key_id)
    if existing_key:
        raise HTTPException(status_code=400, detail=f"Key {key_id} already exists")
    
    public_key = PublicKey(
        key_id=key_id,
        public_key_pem=public_key_pem,
        is_admin=is_admin,
        created_by=created_by,
        domain=domain or config.domain
    )
    session.add(public_key)
    await session.commit()
    await session.refresh(public_key)
    return public_key

async def remove_public_key_from_db(session: AsyncSession, key_id: str) -> bool:
    """Remove a public key from the database"""
    public_key = await get_public_key_by_id(session, key_id)
    if not public_key:
        raise HTTPException(status_code=404, detail=f"Key {key_id} not found")
    
    await session.delete(public_key)
    await session.commit()
    return True

async def get_all_public_keys(session: AsyncSession) -> List[PublicKey]:
    """Get all public keys from the database"""
    result = await session.execute(select(PublicKey))
    return result.scalars().all()

async def get_admin_keys(session: AsyncSession) -> List[PublicKey]:
    """Get all admin keys from the database"""
    result = await session.execute(
        select(PublicKey).where(PublicKey.is_admin == True)
    )
    return result.scalars().all()

async def is_admin_key(session: AsyncSession, key_id: str) -> bool:
    """Check if a key_id is an admin key"""
    public_key = await get_public_key_by_id(session, key_id)
    return public_key.is_admin if public_key else False

# Require admin authentication
async def require_admin_auth(
    key_id: str = Header(...),
    signature: str = Header(...),
    message: str = Header(...),
    session: AsyncSession = Depends(get_db)
):
    """Require admin authentication"""
    # First verify the signature
    await require_signature(key_id, signature, message, session)
    
    # Then check if it's an admin key
    if not await is_admin_key(session, key_id):
        raise HTTPException(status_code=401, detail="Not authorized: not admin key")
    
    return key_id

async def require_signature(
    key_id: str = Header(...),
    signature: str = Header(...),
    message: str = Header(...),
    session: AsyncSession = Depends(get_db)
):
    """Verify signature for any key"""
    # Get the public key from database
    public_key_record = await get_public_key_by_id(session, key_id)
    if not public_key_record:
        raise HTTPException(status_code=401, detail="Key not found")
    
    try:
        # Load the public key
        public_key = serialization.load_pem_public_key(
            public_key_record.public_key_pem.encode(),
            backend=None
        )
        
        # Verify the signature
        signature_bytes = base64.b64decode(signature)
        message_bytes = message.encode()
        
        public_key.verify(signature_bytes, message_bytes)
        
    except (ValueError, InvalidSignature, Exception) as e:
        raise HTTPException(status_code=401, detail=f"Invalid signature: {str(e)}")
    
    return key_id