"""
Tests for key verification functionality.
"""

import pytest
import base64
import logging
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from fastapi import HTTPException

from app.core.security import (
    add_public_key_to_db, 
    require_signature, 
    get_public_key_by_id,
    require_admin_auth
)

logger = logging.getLogger(__name__)

def generate_key_pair(key_id: str):
    """Generate a new Ed25519 key pair"""
    logger.info(f"Generating key pair for key_id: {key_id}")
    
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    public_key_pem = public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo
    ).decode()
    
    logger.info(f"Generated key pair for {key_id}")
    return private_key, public_key_pem


def key_headers(key_id: str, message: str, private_key: Ed25519PrivateKey):
    message = message.encode()
    signature = private_key.sign(message)
    return {
        'key-id': key_id,
        'signature': base64.b64encode(signature).decode(),
        'message': base64.b64encode(message).decode()
    }
@pytest.mark.asyncio
async def test_key_generation_and_storage(db_session):
    """Test generating a key pair and storing it in the database."""
    test_key_id = "test_key_123"
    
    # Generate key pair
    private_key, public_key_pem = generate_key_pair(test_key_id)
    
    # Add to database
    public_key_record = await add_public_key_to_db(
        session=db_session,
        key_id=test_key_id,
        public_key_pem=public_key_pem,
        is_admin=False,
        created_by="test_script",
        domain="test.local"
    )
    
    assert public_key_record.key_id == test_key_id
    assert public_key_record.public_key_pem == public_key_pem
    assert public_key_record.is_admin == False
    
    # Verify retrieval
    retrieved_key = await get_public_key_by_id(db_session, test_key_id)
    assert retrieved_key is not None
    assert retrieved_key.key_id == test_key_id

@pytest.mark.asyncio
async def test_signature_verification(db_session, cleanup_test_keys):
    """Test creating and verifying a signature."""
    test_key_id = "test_key_456"
    test_message = "Hello, this is a test message for signature verification!"
    
    # Generate key pair and add to database
    private_key, public_key_pem = generate_key_pair(test_key_id)
    await add_public_key_to_db(
        session=db_session,
        key_id=test_key_id,
        public_key_pem=public_key_pem,
        is_admin=False,
        created_by="test_script",
        domain="test.local"
    )
    
    # Create signature
    headers = key_headers(test_key_id, test_message, private_key)
    
    # Verify signature
    verified_key_id = await require_signature(
        key_id=test_key_id,
        signature=headers['signature'],
        message=headers['message'],
        session=db_session
    )
    
    assert verified_key_id == test_key_id

@pytest.mark.asyncio
async def test_invalid_signature_rejection(db_session, cleanup_test_keys):
    """Test that invalid signatures are properly rejected."""
    test_key_id = "test_key_789"
    test_message = "Test message for invalid signature test"
    
    # Generate key pair and add to database
    private_key, public_key_pem = generate_key_pair(test_key_id)
    await add_public_key_to_db(
        session=db_session,
        key_id=test_key_id,
        public_key_pem=public_key_pem,
        is_admin=False,
        created_by="test_script",
        domain="test.local"
    )
    
    # Create valid signature
    headers = key_headers(test_key_id, test_message, private_key)
    
    # Test with invalid signature
    invalid_signature = headers['signature'][:-1] + "X"  # Modify last character
    
    with pytest.raises(HTTPException) as exc_info:
        await require_signature(
            key_id=test_key_id,
            signature=invalid_signature,
            message=headers['message'],
            session=db_session
        )
    
    assert exc_info.value.status_code == 401
    assert "Invalid signature" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_wrong_message_rejection(db_session, cleanup_test_keys):
    """Test that signatures with wrong messages are rejected."""
    test_key_id = "test_key_wrong_msg"
    original_message = "Original message"
    wrong_message = "This is a different message"
    
    # Generate key pair and add to database
    private_key, public_key_pem = generate_key_pair(test_key_id)
    await add_public_key_to_db(
        session=db_session,
        key_id=test_key_id,
        public_key_pem=public_key_pem,
        is_admin=False,
        created_by="test_script",
        domain="test.local"
    )
    
    # Create signature for original message
    headers = key_headers(test_key_id, original_message, private_key)
    
    # Try to verify with wrong message
    with pytest.raises(HTTPException) as exc_info:
        await require_signature(
            key_id=test_key_id,
            signature=headers['signature'],
            message=wrong_message,
            session=db_session
        )
    
    assert exc_info.value.status_code == 401
    assert "Invalid signature" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_nonexistent_key_rejection(db_session):
    """Test that verification fails for non-existent keys."""
    fake_key_id = "nonexistent_key"
    fake_signature = "fake_signature"
    fake_message = "fake message"
    
    with pytest.raises(HTTPException) as exc_info:
        await require_signature(
            key_id=fake_key_id,
            signature=fake_signature,
            message=fake_message,
            session=db_session
        )
    
    assert exc_info.value.status_code == 401
    assert "Key not found" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_admin_key_verification(db_session, cleanup_test_keys):
    """Test admin key creation and verification."""
    admin_key_id = "test_admin_key"
    test_message = "Admin test message"
    
    # Generate admin key pair and add to database
    private_key, public_key_pem = generate_key_pair(admin_key_id)
    await add_public_key_to_db(
        session=db_session,
        key_id=admin_key_id,
        public_key_pem=public_key_pem,
        is_admin=True,
        created_by="test_script",
        domain="test.local"
    )
    
    # Create signature
    headers = key_headers(admin_key_id, test_message, private_key)
    
    # Verify as admin
    verified_key_id = await require_admin_auth(
        key_id=admin_key_id,
        signature=headers['signature'],
        message=headers['message'],
        session=db_session
    )
    
    assert verified_key_id == admin_key_id

@pytest.mark.asyncio
async def test_non_admin_key_admin_verification_fails(db_session, cleanup_test_keys):
    """Test that non-admin keys cannot pass admin verification."""
    regular_key_id = "test_regular_key"
    test_message = "Regular key test message"
    
    # Generate regular key pair and add to database
    private_key, public_key_pem = generate_key_pair(regular_key_id)
    await add_public_key_to_db(
        session=db_session,
        key_id=regular_key_id,
        public_key_pem=public_key_pem,
        is_admin=False,
        created_by="test_script",
        domain="test.local"
    )
    
    # Create signature
    headers = key_headers(regular_key_id, test_message, private_key)
    
    # Try to verify as admin (should fail)
    with pytest.raises(HTTPException) as exc_info:
        await require_admin_auth(
            key_id=regular_key_id,
            signature=headers['signature'],
            message=headers['message'],
            session=db_session
        )
    
    assert exc_info.value.status_code == 401
    assert "not admin key" in str(exc_info.value.detail) 