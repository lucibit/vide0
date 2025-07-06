#!/bin/bash

# Setup script for HTTPS with Let's Encrypt

echo "Setting up HTTPS for vide0..."

# Create directories
echo "Creating directories..."
mkdir -p certbot/conf
mkdir -p certbot/www

# Set permissions
echo "Setting permissions..."
chmod 755 certbot/conf
chmod 755 certbot/www

# Update email in docker-compose file
echo "Please update the email address in docker-compose.prod.yml"
echo "Replace 'your-email@example.com' with your actual email address"

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update the email address in docker-compose.prod.yml (replace 'your-email@example.com')"
echo "2. Make sure your domain (from DOMAIN env var) points to your NAS IP"
echo "3. Run: docker-compose -f docker-compose.prod.yml up -d"
echo "4. Check logs: docker-compose -f docker-compose.prod.yml logs certbot"
echo ""
echo "After setup, your app will be available at:"
echo "  HTTPS: https://\${DOMAIN}:8483"
echo "  HTTP will redirect to HTTPS" 