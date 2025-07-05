from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AsyncSessionLocal
from app.core.config import config
from app.core.security import get_admin_keys
import json
import qrcode
import base64
from io import BytesIO

router = APIRouter()

# Templates directory
templates = Jinja2Templates(directory="app/templates")

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

def generate_qr_code(data: dict) -> str:
    """Generate QR code as base64 encoded image"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(json.dumps(data))
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()

@router.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Setup page with QR code for iOS app configuration"""
    # Check if admin keys exist
    admin_keys = await get_admin_keys(db)
    has_admin_keys = len(admin_keys) > 0
    
    # Generate QR code data
    qr_data = config.get_qr_code_data()
    qr_data["has_admin_keys"] = has_admin_keys
    
    # Generate QR code
    qr_code_b64 = generate_qr_code(qr_data)
    
    # Get real client IP for display
    client_ip = config.get_real_client_ip(request)
    
    return templates.TemplateResponse(
        "setup.html",
        {
            "request": request,
            "qr_code": qr_code_b64,
            "qr_data": json.dumps(qr_data, indent=2),
            "domain": config.domain,
            "has_admin_keys": has_admin_keys,
            "client_ip": client_ip,
            "initial_admin_configured": config.has_initial_admin_config()
        }
    )