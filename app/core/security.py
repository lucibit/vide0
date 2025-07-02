import os
import json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from typing import Dict

KEYS_FILE = os.environ.get("KEYS_FILE", "app/keys/whitelist.json")
# For now, the admin key is the first key in the whitelist
ADMIN_KEY_ID = os.environ.get("ADMIN_KEY_ID", "lucibit")  # Optionally set via env

# Ensure keys directory exists
os.makedirs(os.path.dirname(KEYS_FILE), exist_ok=True)

# Load whitelisted public keys from JSON file
def load_whitelisted_keys() -> Dict[str, str]:
    if not os.path.exists(KEYS_FILE):
        return {}
    with open(KEYS_FILE, "r") as f:
        return json.load(f)

# Save whitelisted public keys to JSON file
def save_whitelisted_keys(keys: Dict[str, str]):
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)

# Add a public key to the whitelist
def add_public_key(key_id: str, public_key_pem: str):
    keys = load_whitelisted_keys()
    keys[key_id] = public_key_pem
    save_whitelisted_keys(keys)

# Remove a public key from the whitelist
def remove_public_key(key_id: str):
    keys = load_whitelisted_keys()
    if key_id in keys:
        del keys[key_id]
        save_whitelisted_keys(keys)

# Verify a signature using Ed25519
def verify_signature(key_id: str, message: bytes, signature: bytes) -> bool:
    keys = load_whitelisted_keys()
    public_key_pem = keys.get(key_id)
    if not public_key_pem:
        return False
    public_key = serialization.load_pem_public_key(public_key_pem.encode())
    try:
        public_key.verify(signature, message)
        return True
    except InvalidSignature:
        return False 
    
def get_admin_key_id():
    keys = load_whitelisted_keys()
    if ADMIN_KEY_ID and ADMIN_KEY_ID in keys:
        return ADMIN_KEY_ID
    # fallback: first key in the whitelist
    if keys:
        return next(iter(keys.keys()))
    return None