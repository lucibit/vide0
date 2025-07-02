import os
import argparse
import requests
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend

CHUNK_SIZE = 10 * 1024 * 1024  # 10MB per chunk
ADMIN_KEY_ID = "lucibit"


def split_file(filepath, chunk_size=CHUNK_SIZE):
    chunks = []
    with open(filepath, 'rb') as f:
        i = 1
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunk_path = f"{filepath}.part{i}"
            with open(chunk_path, 'wb') as cf:
                cf.write(chunk)
            chunks.append(chunk_path)
            i += 1
    return chunks

def save_keypair(keys_dir, private_key, key_id):
    os.makedirs(keys_dir, exist_ok=True)
    priv_path = os.path.join(keys_dir, f"{key_id}_private.pem")
    pub_path = os.path.join(keys_dir, f"{key_id}_public.pem")
    with open(priv_path, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        ))
    with open(pub_path, 'wb') as f:
        f.write(private_key.public_key().public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        ))
    print(f"Saved private key to {priv_path}\nSaved public key to {pub_path}")

def generate_keypair(keys_dir, key_id):
    private_key = Ed25519PrivateKey.generate()
    save_keypair(keys_dir, private_key, key_id)
    return private_key

def load_private_key(keys_dir, key_id):
    priv_path = os.path.join(keys_dir, f"{key_id}_private.pem")
    with open(priv_path, 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

def load_public_key(keys_dir, key_id):
    pub_path = os.path.join(keys_dir, f"{key_id}_public.pem")
    with open(pub_path, 'rb') as f:
        return f.read().decode()
    
def key_headers(key_id, private_key):
    message = key_id.encode()
    signature = private_key.sign(message)
    return {
        'key-id': key_id,
        'signature': base64.b64encode(signature).decode(),
        'message': base64.b64encode(message).decode()
    }

def upload_key(server_url, keys_dir, key_id):
    public_key_pem = load_public_key(keys_dir, key_id)
    private_key = load_private_key(keys_dir, ADMIN_KEY_ID)
    headers = key_headers(ADMIN_KEY_ID, private_key)
    resp = requests.post(f"{server_url}/auth/whitelist/add", data={
        'key_id': key_id,
        'public_key_pem': public_key_pem
    }, headers=headers)
    print(resp.status_code, resp.text)

def upload_file(server_url, keys_dir, filepath, key_id):
    private_key = load_private_key(keys_dir, key_id)
    # Split file
    chunks = split_file(filepath)
    total_chunks = len(chunks)
    filename = os.path.basename(filepath)
    print(f"Split into {total_chunks} chunks.")

    # Initiate upload
    message = f"initiate:{filename}:{total_chunks}".encode()
    signature = private_key.sign(message)
    headers = key_headers(key_id, private_key)
    resp = requests.post(f"{server_url}/upload/initiate", data={
        'filename': filename,
        'total_chunks': total_chunks
    }, headers=headers)
    resp.raise_for_status()
    upload_id = resp.json()['upload_id']
    print(f"Upload ID: {upload_id}")

    # Upload chunks
    for i, chunk_path in enumerate(chunks, 1):
        message = f"chunk:{upload_id}:{i}:{total_chunks}".encode()
        signature = private_key.sign(message)
        headers = {
            'key_id': key_id,
            'signature': base64.b64encode(signature).decode(),
            'message': base64.b64encode(message).decode()
        }
        with open(chunk_path, 'rb') as f:
            files = {'file': (os.path.basename(chunk_path), f)}
            data = {
                'upload_id': upload_id,
                'chunk_number': i,
                'total_chunks': total_chunks
            }
            resp = requests.post(f"{server_url}/upload/chunk", data=data, files=files, headers=headers)
            resp.raise_for_status()
            print(f"Uploaded chunk {i}/{total_chunks}")

    # Complete upload
    message = f"complete:{upload_id}".encode()
    signature = private_key.sign(message)
    headers = key_headers(key_id, private_key)
    resp = requests.post(f"{server_url}/upload/complete", data={
        'upload_id': upload_id
    }, headers=headers)
    resp.raise_for_status()
    print("Upload complete! Video link:", resp.json().get('video_link'))

    # Clean up chunk files
    for chunk_path in chunks:
        os.remove(chunk_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chunked video uploader client.")
    parser.add_argument('--server-url', help='Base URL of the FastAPI server, e.g. http://localhost:8000')
    parser.add_argument('--keys-dir', help='Directory to save keys, defaults to keys')
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # Mode: generate-key
    genkey_parser = subparsers.add_parser("generate-key", help="Generate a new key pair and save to disk.")
    genkey_parser.add_argument("key_id", help="Key ID to use for the new key pair.")
    genkey_parser.add_argument("--upload", action="store_true", help="Also upload the public key to the server.")

    upload_key_parser = subparsers.add_parser("upload-key", help="Upload existing public key to the server.")
    upload_key_parser.add_argument('key_id', help='Key ID to use for signing')

    # Mode: upload
    upload_parser = subparsers.add_parser("upload-video", help="Upload a video file using a key.")
    upload_parser.add_argument('filepath', help='Path to the video file to upload')
    upload_parser.add_argument('key_id', help='Key ID to use for signing')

    args = parser.parse_args()
    if not args.keys_dir:
        print("--keys-dir is required")
        exit(1)

    if args.mode == "generate-key":
        private_key = generate_keypair(keys_dir=args.keys_dir, key_id=args.key_id)
        if args.upload:
            if not args.server_url:
                print("--server-url is required when using --upload")
            else:
                upload_key(server_url=args.server_url, keys_dir=args.keys_dir, key_id=args.key_id)
    elif args.mode == "upload-key":
        upload_key(server_url=args.server_url, keys_dir=args.keys_dir, key_id=args.key_id)
    elif args.mode == "upload-video":
        upload_file(server_url=args.server_url, keys_dir=args.keys_dir, filepath=args.filepath, key_id=args.key_id) 