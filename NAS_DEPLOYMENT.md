# Synology NAS Deployment Guide

## Prerequisites
- Synology NAS with Docker support
- SSH access to your NAS (optional, but recommended)
- Your admin public key file (`lucibit_public.pem`)

## Step 1: Prepare Your Local Environment

1. **Build and push the Docker image** (already done):
   ```bash
   docker build -t lucibit/vide0:latest .
   docker push lucibit/vide0:latest
   ```

2. **Copy your admin public key** to a location you can access from your NAS.

## Step 2: Deploy to Synology NAS

### Option A: Using Synology Container Manager (GUI)

1. **Open Container Manager** on your Synology DSM
2. **Click "Add" → "Add using Docker Compose"**
3. **Upload the `docker-compose.prod.yml` file**
4. **Create the required directories** via SSH or File Station:
   ```bash
   mkdir -p /volume1/Media/vide0
   ```
5. **Copy your admin public key** to `/volume1/Media/vide0/admin_public.pem`
6. **Update the DOMAIN environment variable** in the compose file to match your NAS domain
7. **Deploy the containers**

### Option B: Using SSH (Recommended)

1. **SSH into your NAS**:
   ```bash
   ssh admin@your-nas-ip
   ```

2. **Create a directory for the project**:
   ```bash
   mkdir -p /volume1/docker/vide0
   cd /volume1/docker/vide0
   ```

3. **Copy the required files** from your local machine:
   ```bash
   # From your local machine, copy these files to the NAS:
   scp docker-compose.prod.yml admin@your-nas-ip:/volume1/docker/vide0/
   scp nginx.conf admin@your-nas-ip:/volume1/docker/vide0/
   scp lucibit_public.pem admin@your-nas-ip:/volume1/docker/vide0/keys/admin_public.pem
   ```

4. **Create directories and set permissions**:
   ```bash
   mkdir -p /volume1/docker/vide0
   chmod 755 /volume1/docker/vide0
   ```

5. **Update the DOMAIN** in `docker-compose.prod.yml`:
   ```bash
   sed -i 's/your-nas-domain.local/YOUR_ACTUAL_NAS_DOMAIN/g' docker-compose.prod.yml
   ```

6. **Deploy the containers**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Step 3: Verify Deployment

1. **Check container status**:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

2. **Check logs**:
   ```bash
   docker-compose -f docker-compose.prod.yml logs app
   ```

3. **Access the application**:
   - Open your browser and go to `http://your-nas-ip`
   - You should see the vide0 setup page

## Step 4: Configure Your Upload Client

Update your upload client configuration to point to your NAS:

```bash
python upload_client.py --keys-dir ../tmp/upload-keys --server-url http://your-nas-ip upload-video /path/to/video.mp4 lucibit
```

## Troubleshooting

### Container won't start
- Check logs: `docker-compose -f docker-compose.prod.yml logs app`
- Verify the admin public key file exists and is readable
- Check that all directories exist and have proper permissions

### Can't access the web interface
- Verify nginx is running: `docker-compose -f docker-compose.prod.yml ps`
- Check nginx logs: `docker-compose -f docker-compose.prod.yml logs nginx`
- Ensure ports 80 and 443 are not blocked by firewall

### Upload fails
- Check that the admin public key in the container matches your local key
- Verify the key was properly loaded during container startup
- Check app logs for signature verification errors

## Security Considerations

1. **Change default ports** if needed by modifying the docker-compose file
2. **Use HTTPS** by adding SSL certificates to nginx
3. **Restrict access** by configuring firewall rules
4. **Regular backups** of the `/volume1/docker/vide0/data` directory

## Maintenance

- **Update the image**: Pull the latest version and restart containers
- **Backup data**: Regularly backup the SQLite database and uploaded videos
- **Monitor logs**: Check container logs periodically for issues 