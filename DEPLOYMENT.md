# Video Server Deployment Guide

This guide explains how to deploy the video server with Docker Compose and nginx reverse proxy.

## Prerequisites

- Docker and Docker Compose installed
- Access to your NAS directory for video storage

## Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Domain for the application (used in setup QR codes)
DOMAIN=your-domain.com


# Path to your NAS mount point
NAS_MOUNT_PATH=/path/to/your/nas/videos

# Initial admin key configuration (optional)
INITIAL_ADMIN_KEY_ID=admin
INITIAL_ADMIN_PUBLIC_KEY_NAME=admin_public.pem
```

## Initial Admin Key Setup

### Option 1: Environment Variables (Recommended)

Set the initial admin key via environment variables when starting the container:

```bash
# Generate a key pair first
python upload_client.py generate-key admin

# Add to your .env file
INITIAL_ADMIN_KEY_ID=admin
INITIAL_ADMIN_PUBLIC_KEY_NAME=admin_public.pem

The admin key will be automatically created when the container starts.

### Option 2: Manual Setup

If you don't set environment variables, you can create admin keys manually using the client script:

```bash
# Generate a key pair
python upload_client.py generate-key admin

# Upload the key (requires existing admin key)
python upload_client.py upload-key admin --admin
```

## Quick Start

1. **Clone and setup the project:**
   ```bash
   git clone <your-repo>
   cd vide0
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start the services:**
   ```bash
   docker-compose up -d
   ```

4. **Check the logs:**
   ```bash
   docker-compose logs -f
   ```

## Services

The Docker Compose setup includes:

- **nginx**: Reverse proxy handling external requests and forwarding headers
- **app**: FastAPI application running on port 8000 (internal)

### Nginx Configuration

The nginx reverse proxy:
- Handles large file uploads (up to 10GB)
- Forwards proper client IP headers for local network detection
- Optimizes video streaming with range requests
- Provides security headers
- Routes all traffic to the FastAPI application

### Network Architecture

```
Internet → nginx:80 → app:8000
```

The nginx proxy properly sets:
- `X-Real-IP`: Client's real IP address
- `X-Forwarded-For`: Chain of IP addresses
- `X-Forwarded-Proto`: Original protocol (http/https)

## Setup Page

Access the setup page to get QR codes for iOS app configuration:

```
http://your-server-ip/setup
```

The setup page shows:
- Admin key status
- QR code for iOS app configuration
- Configuration data for manual setup

## Video Storage

Videos are stored in the mounted NAS directory:
- Database: `/nas/videos/db.sqlite3`
- Video files: `/nas/videos/videos/`
- Chunk uploads: `/nas/videos/chunks/`

## Client Usage

Use the client script to interact with the server:

```bash
# Generate a new key pair
python upload_client.py generate-key <key_id>

# Upload a key (requires admin key)
python upload_client.py upload-key <key_id> <public_key_pem>

# Upload a video
python upload_client.py upload <video_path>
```

## Troubleshooting

### Admin Key Issues

If admin keys aren't being created:

1. **Check environment variables:**
   ```bash
   docker-compose exec app env | grep INITIAL_ADMIN
   ```

2. **Check application logs:**
   ```bash
   docker-compose logs app | grep "admin key"
   ```

3. **Verify key format:**
   - Ensure the public key is in PEM format
   - Include the full key including headers


### Large File Upload Issues

If uploads fail:

1. **Check nginx logs:**
   ```bash
   docker-compose logs nginx
   ```

2. **Verify client_max_body_size** in nginx.conf (currently 10GB)

3. **Check available disk space** on your NAS

### Database Issues

If the database isn't accessible:

1. **Check volume mount:**
   ```bash
   docker-compose exec app ls -la /nas/videos/
   ```

2. **Verify permissions** on the NAS directory

3. **Check app logs:**
   ```bash
   docker-compose logs app
   ```

## Security Considerations

- Admin keys are required for key management
- All video uploads require valid signatures
- The nginx proxy adds security headers
- Consider using HTTPS in production
- Initial admin keys are created from environment variables

## Production Deployment

For production:

1. **Add SSL/TLS certificates**
2. **Use environment-specific settings**
3. **Set up proper logging**
4. **Configure backups for the database**
5. **Monitor disk space usage**

## Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Rebuild and restart
docker-compose up -d --build

# Access app shell
docker-compose exec app bash

# Access nginx shell
docker-compose exec nginx sh
``` 