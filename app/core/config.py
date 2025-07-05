import os
from fastapi import Request
import logging

class Config:
    """Application configuration"""
    
    def __init__(self):
        self.domain = os.environ.get("DOMAIN", "localhost:8000")
        
        # Initial admin key configuration
        self.initial_admin_key_id = os.environ.get("INITIAL_ADMIN_KEY_ID")
        
        self.nas_mount_path = "/nas/videos"
        self.initial_admin_public_key_file_name = os.path.join(self.nas_mount_path, os.environ.get("INITIAL_ADMIN_PUBLIC_KEY_FILE_NAME"))
        self.chunks_dir = os.path.join(self.nas_mount_path, "chunks")
        self.videos_dir = os.path.join(self.nas_mount_path, "videos")
        os.makedirs(self.chunks_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)

    
    def get_real_client_ip(self, request: Request) -> str:
        """Extract real client IP from request, handling proxy headers"""
        # Check for X-Real-IP first (set by nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Check for forwarded headers (set by reverse proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, first one is the original client
            first_ip = forwarded_for.split(",")[0].strip()
            return first_ip
        
        # Fallback to direct client IP (works for direct access)
        client_ip = request.client.host if request.client else "unknown"
        return client_ip
        
    
    def get_server_url(self, use_https: bool = True) -> str:
        """Get the server URL for the domain"""
        protocol = "https" if use_https else "http"
        return f"{protocol}://{self.domain}"
    
    def get_qr_code_data(self) -> dict:
        """Get data for QR code generation"""
        return {
            "domain": self.domain,
            "server_url": self.get_server_url(),
            "setup_url": f"{self.get_server_url()}/setup",
            "auth_api_base": f"{self.get_server_url()}/auth"
        }
    
    def has_initial_admin_config(self) -> bool:
        """Check if initial admin key is configured via environment"""
        return bool(self.initial_admin_key_id and self.initial_admin_public_key_file_name and os.path.exists(self.initial_admin_public_key_file_name))
    
    def get_initial_admin_public_key(self) -> str:
        """Load the initial admin public key from file"""
        if not self.initial_admin_public_key_file_name:
            logging.info("No initial admin public key file configured")
            return None
            
        logging.info(f"Loading initial admin public key from {self.initial_admin_public_key_file_name}")
        
        try:
            with open(self.initial_admin_public_key_file_name, 'r') as f:
                return f.read().strip()
        except Exception as e:
            return None

# Dependency injection function
def get_config() -> Config:
    """Get a config instance for dependency injection"""
    return Config() 