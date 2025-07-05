from fastapi import APIRouter, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import (
    add_public_key_to_db, 
    require_admin_auth,
    remove_public_key_from_db, 
    get_all_public_keys,
    get_db
)

router = APIRouter()

@router.post("/auth/whitelist/add")
async def api_add_key(
    key_id: str = Form(...),
    public_key_pem: str = Form(...),
    is_admin: bool = Form(False),
    admin: str = Depends(require_admin_auth),
    session: AsyncSession = Depends(get_db)
):
    await add_public_key_to_db(session, key_id, public_key_pem, is_admin, admin)
    return {"status": "added", "key_id": key_id, "is_admin": is_admin}

@router.post("/auth/whitelist/remove")
async def api_remove_key(
    key_id: str = Form(...),
    admin: str = Depends(require_admin_auth),
    session: AsyncSession = Depends(get_db)
):
    await remove_public_key_from_db(session, key_id)
    return {"status": "removed", "key_id": key_id}

@router.get("/auth/whitelist/list")
async def api_list_keys(
    admin: str = Depends(require_admin_auth),
    session: AsyncSession = Depends(get_db)
):
    keys = await get_all_public_keys(session)
    return {
        key.key_id: {
            "public_key_pem": key.public_key_pem,
            "is_admin": key.is_admin,
            "created_at": key.created_at.isoformat() if key.created_at else None,
            "created_by": key.created_by
        }
        for key in keys
    } 