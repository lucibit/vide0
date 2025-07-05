import asyncio, logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AsyncSessionLocal
from app.core.config import get_config
from app.core.security import get_admin_keys, add_public_key_to_db

# Configure logging to output to stdout
logging.basicConfig(level=logging.INFO, format='%(message)s')

async def create_initial_admin_key():
    """Create initial admin key from environment variables if configured"""
    config = get_config()
    if not config.has_initial_admin_config():
        logging.info("No initial admin key configuration found in environment variables")
        return
    
    async with AsyncSessionLocal() as session:
        # Check if admin keys already exist
        existing_admin_keys = await get_admin_keys(session)
        if existing_admin_keys:
            logging.info(f"Admin keys already exist ({len(existing_admin_keys)} found), skipping initial admin key creation")
            return
        
        try:
            # Load the public key from file
            public_key_pem = config.get_initial_admin_public_key()
            if not public_key_pem:
                logging.error(f"❌ Failed to load initial admin public key from {config.initial_admin_public_key_file_name}")
                return
            
            # Create the initial admin key
            await add_public_key_to_db(
                session=session,
                key_id=config.initial_admin_key_id,
                public_key_pem=public_key_pem,
                is_admin=True,
                created_by="startup_script",
                domain=config.domain,
                config=config
            )
            logging.info(f"✅ Successfully created initial admin key '{config.initial_admin_key_id}'")
        except Exception as e:
            logging.error(f"❌ Failed to create initial admin key: {e}")

async def startup_event():
    """Run startup tasks"""
    logging.info("🚀 Starting video server...")
    await create_initial_admin_key()
    logging.info("✅ Startup complete") 