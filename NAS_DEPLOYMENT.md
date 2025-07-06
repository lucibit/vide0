# Synology NAS Deployment Guide with HTTPS

## Prerequisites
- Synology NAS with Docker support
- SSH access to your NAS (recommended)
- Your admin public key file (`admin_public.pem`)
- A domain name that points to your NAS IP address
- Ports 8081 and 8483 accessible from the internet (for Let's Encrypt verification)

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
   mkdir -p /volume1/Media/vide0/certbot/conf
   mkdir -p /volume1/Media/vide0/certbot/www
   ```
5. **Copy your admin public key** to `/volume1/Media/vide0/admin_public.pem`
6. **Update the DOMAIN environment variable** in the compose file to match your domain
7. **Update the email address** in the compose file (replace `your-email@example.com`)
8. **Deploy the containers**

### Option B: Using SSH (Recommended)

1. **SSH into your NAS**:
   ```bash
   ssh admin@your-nas-ip
   ```

2. **Create a directory for the project**:
   ```bash
   mkdir -p /volume1/Media/vide0
   cd /volume1/Media/vide0
   ```

3. **Copy the required files** from your local machine:
   ```bash
   # From your local machine, copy these files to the NAS:
   scp docker-compose.prod.yml admin@your-nas-ip:/volume1/Media/vide0/
   scp nginx.template.conf admin@your-nas-ip:/volume1/Media/vide0/
   scp setup_https.sh admin@your-nas-ip:/volume1/Media/vide0/
   scp renew_ssl.sh admin@your-nas-ip:/volume1/Media/vide0/
   scp admin_public.pem admin@your-nas-ip:/volume1/Media/vide0/admin_public.pem
   ```

4. **Run the setup script**:
   ```bash
   chmod +x setup_https.sh
   ./setup_https.sh
   ```

5. **Update the configuration**:
   ```bash
   # Update DOMAIN in docker-compose.prod.yml
   sed -i 's/DOMAIN=domain.example.com/DOMAIN=your-actual-domain.com/g' docker-compose.prod.yml
   
   # Update email address in docker-compose.prod.yml
   sed -i 's/your-email@example.com/your-actual-email@example.com/g' docker-compose.prod.yml
   ```

6. **Deploy the containers**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Step 3: Verify HTTPS Setup

1. **Check container status**:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

2. **Check certificate generation**:
   ```bash
   docker-compose -f docker-compose.prod.yml logs certbot
   ```

3. **Test HTTPS access**:
   - **HTTP redirect**: Visit `http://your-domain:8081` (should redirect to HTTPS)
   - **HTTPS direct**: Visit `https://your-domain:8483/setup`
   - **Certificate check**: `openssl s_client -connect your-domain:8483 -servername your-domain`

4. **Check nginx logs**:
   ```bash
   docker-compose -f docker-compose.prod.yml logs nginx
   ```

## Step 4: Configure Your Upload Client

Update your upload client to use HTTPS:

```bash
python upload_client.py --keys-dir ../tmp/upload-keys --server-url https://your-domain:8483 upload-video /path/to/video.mp4 lucibit
```

## SSL Certificate Management

### Automatic Renewal
Let's Encrypt certificates expire after 90 days. Set up automatic renewal:

1. **Add to crontab** (run every 60 days):
   ```bash
   crontab -e
   # Add this line:
   0 2 */60 * * /volume1/docker/vide0/renew_ssl.sh
   ```

2. **Manual renewal**:
   ```bash
   chmod +x renew_ssl.sh
   ./renew_ssl.sh
   ```

## Troubleshooting

### Certificate Generation Fails
- Check that your domain resolves to the correct IP: `nslookup your-domain`
- Verify ports 8081 and 8483 are accessible from the internet
- Check certbot logs: `docker-compose -f docker-compose.prod.yml logs certbot`
- Ensure your NAS is accessible from the internet for Let's Encrypt verification

### HTTPS Not Working
- Verify SSL certificate files exist: `ls -la certbot/conf/live/your-domain/`
- Check nginx logs: `docker-compose -f docker-compose.prod.yml logs nginx`
- Ensure nginx configuration is correct
- Check that the domain in docker-compose matches your actual domain

### Container won't start
- Check logs: `docker-compose -f docker-compose.prod.yml logs app`
- Verify the admin public key file exists and is readable
- Check that all directories exist and have proper permissions

### Upload fails
- Check that the admin public key in the container matches your local key
- Verify the key was properly loaded during container startup
- Check app logs for signature verification errors
- Ensure you're using HTTPS URLs in your upload client

### Can't access the web interface
- Verify nginx is running: `docker-compose -f docker-compose.prod.yml ps`
- Check nginx logs: `docker-compose -f docker-compose.prod.yml logs nginx`
- Ensure ports 8081 and 8483 are not blocked by firewall
- Try accessing via HTTPS: `https://your-domain:8483`

## Security Benefits

With HTTPS enabled, you get:
- ✅ Encrypted communication
- ✅ WhatsApp link previews will work
- ✅ Better security for file uploads
- ✅ Modern browser features
- ✅ SEO benefits

## Port Configuration

- **HTTP**: Port 8081 (redirects to HTTPS)
- **HTTPS**: Port 8483 (main access)
- **Internal FastAPI**: Port 8081 (container network only)

## Security Considerations

1. **HTTPS is mandatory** - all communication is encrypted
2. **Automatic certificate renewal** - certificates are managed by Let's Encrypt
3. **Restrict access** by configuring firewall rules
4. **Regular backups** of the `/volume1/Media/vide0` directory
5. **Monitor logs** for security issues

## Maintenance

- **Update the image**: Pull the latest version and restart containers
- **Backup data**: Regularly backup the SQLite database and uploaded videos
- **Monitor logs**: Check container logs periodically for issues
- **Certificate renewal**: Set up automatic renewal or renew manually every 90 days

## Files Structure

```
/volume1/docker/vide0/
├── docker-compose.prod.yml
├── nginx.template.conf
├── setup_https.sh
├── renew_ssl.sh
└── certbot/
    ├── conf/          # SSL certificates
    └── www/           # Let's Encrypt challenge files

/volume1/Media/vide0/
├── admin_public.pem   # Admin public key
└── videos/            # Uploaded videos
``` 