"""
Pytest configuration and fixtures for the video server tests.
"""

import pytest
import asyncio
import logging
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models import AsyncSessionLocal, init_db
from app.core.security import remove_public_key_from_db


# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

import pytest_asyncio

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    DATABASE_URL = 'sqlite+aiosqlite:///:memory:'
    engine = create_async_engine(DATABASE_URL, echo=False)
    await init_db(engine)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine):
    """Provide a database session for tests."""
    async with sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )() as session:
        yield session

@pytest_asyncio.fixture
async def cleanup_test_keys():
    """Cleanup fixture to remove test keys after tests."""
    yield
    # Cleanup test keys after test
    async with AsyncSessionLocal() as session:
        test_keys = ["test_key_123", "test_key_456", "test_admin_key", "test_key_789", "test_key_wrong_msg", "test_regular_key"]
        for key_id in test_keys:
            try:
                await remove_public_key_from_db(session, key_id)
            except Exception:
                pass  # Key might not exist, that's fine 