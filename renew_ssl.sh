#!/bin/bash

# SSL Certificate Renewal Script

echo "Renewing SSL certificate..."

# Stop nginx temporarily
docker-compose -f docker-compose.prod.yml stop nginx

# Renew certificate
docker-compose -f docker-compose.prod.yml run --rm certbot renew

# Start nginx again
docker-compose -f docker-compose.prod.yml up -d nginx

echo "SSL certificate renewal complete!" 