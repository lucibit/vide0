from fastapi import APIRouter, HTTPException, Depends, Header, Form
from app.core.security import add_public_key, get_admin_key_id, remove_public_key, load_whitelisted_keys, verify_signature
import base64

router = APIRouter()


def admin_signature_auth(
    key_id: str = Header(...),
    signature: str = Header(...),
    message: str = Header(...)
):
    admin_key_id = get_admin_key_id()
    if not admin_key_id or key_id != admin_key_id:
        raise HTTPException(status_code=401, detail="Not authorized: not admin key")
    try:
        signature_bytes = base64.b64decode(signature)
        message_bytes = base64.b64decode(message)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 encoding for signature or message")
    if not verify_signature(key_id, message_bytes, signature_bytes):
        raise HTTPException(status_code=401, detail="Invalid signature or key not whitelisted")
    return key_id

@router.post("/auth/whitelist/add")
def api_add_key(
    key_id: str = Form(...),
    public_key_pem: str = Form(...),
    admin: str = Depends(admin_signature_auth)
):
    add_public_key(key_id, public_key_pem)
    return {"status": "added", "key_id": key_id}

@router.post("/auth/whitelist/remove")
def api_remove_key(
    key_id: str = Form(...),
    admin: str = Depends(admin_signature_auth)
):
    remove_public_key(key_id)
    return {"status": "removed", "key_id": key_id}

@router.get("/auth/whitelist/list")
def api_list_keys(admin: str = Depends(admin_signature_auth)):
    return load_whitelisted_keys() 