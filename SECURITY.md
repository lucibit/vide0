# Security Model & Considerations

This document explains the security model of the video server application, particularly focusing on the admin key setup process.

## Security Overview

The application uses a **environment-based admin setup** model where:
- Initial admin keys are created from environment variables during container startup
- Once admin keys exist, all key management requires existing admin authentication
- The setup page provides QR codes for iOS app configuration but doesn't create admin keys

## Admin Key Setup

### Environment-Based Setup (Recommended)

The most secure approach is to configure the initial admin key via environment variables:

```bash
# Generate a key pair
python upload_client.py generate-key admin

# Set environment variables
INITIAL_ADMIN_KEY_ID=admin
INITIAL_ADMIN_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----..."

# Start container
docker-compose up -d
```

The admin key is automatically created when the container starts, ensuring the system is immediately secure.

### Manual Setup (Alternative)

If environment variables aren't used, admin keys can be created manually using the client script:

```bash
# Generate and upload admin key
python upload_client.py generate-key admin
python upload_client.py upload-key admin --admin
```

## Local Network Detection

### How It Works

The application detects local network access through:

1. **Real IP Headers**: Uses `X-Real-IP` and `X-Forwarded-For` headers set by nginx
2. **Direct Client IP**: Uses the direct client connection IP

### Docker Network Considerations

In Docker environments, the real client IP is properly forwarded by nginx, so local network detection works reliably.

## Security Features

### Access Control

- **Setup Page**: Read-only, shows QR codes and configuration status
- **Admin Key Creation**: Only via environment variables or existing admin authentication
- **Key Management**: Requires existing admin authentication

### Validation Layers

1. **IP Address Validation**: Ensures IPs are valid
2. **Local Network Check**: Validates against configured CIDR range
3. **Admin Key State Check**: Prevents unauthorized admin key creation
4. **Request Logging**: Comprehensive logging of all security-relevant events

## Security Risks & Mitigations

### 1. Environment Variable Exposure

**Risk**: Environment variables containing admin keys could be exposed.

**Mitigations**:
- **Secure Environment**: Use Docker secrets or secure environment management
- **Key Rotation**: Rotate admin keys periodically
- **Access Control**: Limit access to environment configuration

**Risk Level**: **LOW** - Mitigated by proper environment management

### 2. Unauthorized Access

**Risk**: Someone could access the system without proper authentication.

**Mitigations**:
- **Admin Key Requirement**: All key management requires admin authentication
- **Signature Verification**: All operations require valid cryptographic signatures
- **Network Security**: Secure your local network with proper firewall rules

**Risk Level**: **LOW** - Strong authentication requirements

### 3. Key Compromise

**Risk**: Admin keys could be compromised.

**Mitigations**:
- **Key Storage**: Store private keys securely
- **Key Rotation**: Implement regular key rotation procedures
- **Monitoring**: Monitor for unusual access patterns

**Risk Level**: **MEDIUM** - Mitigated by proper key management

## Deployment Security Recommendations

### 1. Use HTTPS in Production

```bash
# Add SSL certificate to nginx
# Update DOMAIN environment variable to use https://
```

### 2. Secure Environment Variables

```bash
# Use Docker secrets or secure environment management
# Never commit .env files to version control
```

### 3. Configure Firewall

```bash
# Only allow access from your local network
# Block external access to sensitive endpoints
```

### 4. Monitor Logs

```bash
# Check application logs for suspicious activity
docker-compose logs app | grep "admin"
```

### 5. Use Strong Admin Keys

- Generate keys with sufficient entropy
- Store private keys securely
- Rotate keys periodically

## Attack Scenarios

### Scenario 1: Environment Variable Exposure

**What they could try**:
- Access environment variables containing admin keys

**Why it's mitigated**:
- Environment variables are isolated within the container
- Proper access controls prevent unauthorized access
- Key rotation procedures limit exposure window

### Scenario 2: Unauthorized Key Creation

**What they could try**:
- Attempt to create admin keys without proper authentication

**Why it fails**:
- All key management requires existing admin authentication
- Cryptographic signatures prevent unauthorized operations
- No web interface for key creation

### Scenario 3: Network Attacks

**What they could try**:
- Access the system from unauthorized networks

**Why it's mitigated**:
- Local network detection provides additional security layer
- Firewall rules can restrict access
- All operations require valid authentication

## Best Practices

### 1. Initial Setup

1. **Use Environment Variables**: Configure initial admin key via environment variables
2. **Generate Strong Keys**: Use the client script to generate secure key pairs
3. **Secure Storage**: Store private keys securely and never share them
4. **Verify Setup**: Test admin key functionality before deploying

### 2. Ongoing Security

1. **Monitor Logs**: Regularly check for suspicious access attempts
2. **Use HTTPS**: Enable SSL/TLS in production
3. **Network Security**: Secure your local network with proper firewall rules
4. **Key Management**: Rotate admin keys periodically

### 3. Production Deployment

2. **Restrict Access**: Use firewall rules to limit access
3. **Backup Keys**: Securely backup admin keys
4. **Monitor Access**: Set up monitoring for unusual access patterns

## Configuration

### Environment Variables

```bash
# Domain for the application
DOMAIN=synology.lucibit.net

# NAS mount path
NAS_MOUNT_PATH=/nas/videos

# Initial admin key configuration
INITIAL_ADMIN_KEY_ID=admin
INITIAL_ADMIN_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----..."
```

### Network Configuration

**Common Local Network Ranges**:
- `192.168.1.0/24` - Common home router range
- `192.168.0.0/16` - Broader home network range
- `10.0.0.0/8` - Private network range
- `172.16.0.0/12` - Docker default range

## Conclusion

The security model prioritizes **practical security** and **ease of deployment**. By using environment variables for initial admin key setup:

- **Eliminates complex local network detection** for admin key creation
- **Provides immediate security** when the container starts
- **Maintains strong authentication** for all operations
- **Simplifies deployment** while maintaining security

The system is designed to be secure by default while remaining easy to deploy and manage. 