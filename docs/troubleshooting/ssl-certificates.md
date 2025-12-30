# SSL Certificate Troubleshooting

This guide covers common SSL certificate issues and solutions for the iChrisBirch application using Traefik and mkcert.

## 🔒 Overview

The application uses a **two-tier certificate strategy**:

1. **mkcert (Preferred)**: Browser-trusted certificates for local development
2. **OpenSSL (Fallback)**: Self-signed certificates when mkcert unavailable

## 🚨 Common SSL Certificate Issues

### 1. Browser Security Warnings

**Problem**: Browser shows "Not Secure" or "Your connection is not private"

**Error Messages**:

```text
NET::ERR_CERT_AUTHORITY_INVALID
ERR_SSL_KEY_USAGE_INCOMPATIBLE  
SSL_ERROR_SELF_SIGNED_CERT
```

**Root Cause**: Using self-signed certificates without proper browser trust

**Resolution**: Install and use mkcert for browser-trusted certificates

```bash
# Install mkcert (macOS)
brew install mkcert

# Install mkcert (Linux)
curl -JLO "https://dl.filippo.io/mkcert/latest?for=linux/amd64"
chmod +x mkcert-v*-linux-amd64
sudo cp mkcert-v*-linux-amd64 /usr/local/bin/mkcert

# Install the local Certificate Authority
mkcert -install

# Regenerate certificates with mkcert
ichrisbirch ssl-manager generate dev

# Restart environment to use new certificates
ichrisbirch dev restart
```

**Prevention**: Always use mkcert for local development to avoid browser warnings

### 2. Certificate Validation Errors

**Problem**: OpenSSL reports certificate validation failures

**Error Messages**:

```text
certificate verify failed: self signed certificate
SSL routines:tls_process_server_certificate:certificate verify failed
```

**Root Cause**: Self-signed certificates don't have valid certificate chain

**Attempted Solutions (That Failed)**:

- Adding `-k` flag to curl commands (bypasses verification but doesn't solve browser issues)
- Manually importing certificates to browser (temporary fix, not scalable)

**Resolution**: Use mkcert for properly signed certificates with valid certificate chain

```bash
# Verify mkcert is installed and working
mkcert -install

# Check certificate authority status
mkcert -CAROOT

# Regenerate certificates
ichrisbirch ssl-manager generate dev

# Verify certificate information
ichrisbirch ssl-manager info dev
```

**Prevention**: Always prefer mkcert over OpenSSL for local development certificates

### 3. Certificate Domain Mismatch

**Problem**: Certificate domain doesn't match requested domain

**Error Messages**:

```text
certificate is valid for *.example.com, not api.docker.localhost
ERR_CERT_COMMON_NAME_INVALID
```

**Root Cause**: Certificate Subject Alternative Names (SANs) don't include the requested domain

**Resolution**: Regenerate certificates with proper domain coverage

```bash
# Check which domains are covered by current certificate
ichrisbirch ssl-manager info dev

# Regenerate with proper SANs (automatically includes all required domains)
ichrisbirch ssl-manager generate dev
```

**Prevention**: The ssl-manager script automatically includes all required domains when generating certificates

### 4. Certificate Expiration

**Problem**: Certificate has expired or is nearing expiration

**Error Messages**:

```text
certificate has expired
SSL_ERROR_EXPIRED_CERT
```

**Root Cause**: Certificate validity period has passed

**Resolution**: Regenerate certificates

```bash
# Check certificate expiration
ichrisbirch ssl-manager info dev

# Regenerate certificates (mkcert certificates last 2+ years)
ichrisbirch ssl-manager generate dev

# Restart to use new certificates
ichrisbirch dev restart
```

**Prevention**: mkcert certificates have much longer validity (2+ years) compared to OpenSSL (365 days)

### 5. mkcert Not Found

**Problem**: mkcert command not found when trying to generate certificates

**Error Messages**:

```text
mkcert: command not found
[INFO] mkcert not found, falling back to OpenSSL
```

**Root Cause**: mkcert not installed on the system

**Resolution**: Install mkcert

```bash
# macOS installation
brew install mkcert

# Linux installation
curl -JLO "https://dl.filippo.io/mkcert/latest?for=linux/amd64"
chmod +x mkcert-v*-linux-amd64
sudo cp mkcert-v*-linux-amd64 /usr/local/bin/mkcert

# Windows installation (using Chocolatey)
choco install mkcert

# Verify installation
mkcert -version

# Install the local CA
mkcert -install
```

**Prevention**: Install mkcert as part of initial development environment setup

### 6. Certificate Authority Not Trusted

**Problem**: mkcert generates certificates but browsers still show warnings

**Error Messages**:

```text
NET::ERR_CERT_AUTHORITY_INVALID
The certificate is not trusted because the issuer certificate is unknown
```

**Root Cause**: mkcert local CA not installed in system trust stores

**Resolution**: Install mkcert CA properly

```bash
# Install the local Certificate Authority
mkcert -install

# Verify CA installation
mkcert -CAROOT

# Check if CA is in system trust store (macOS)
security find-certificate -c "mkcert" -p /Library/Keychains/System.keychain

# Restart browser after CA installation
# Chrome/Safari: Restart completely
# Firefox: Restart or clear certificate cache
```

**Prevention**: Always run `mkcert -install` after installing mkcert

### 7. Wrong Certificate File Permissions

**Problem**: Traefik can't read certificate files

**Error Messages**:

```text
unable to load X509 key pair: open /etc/traefik/certs/dev.key: permission denied
```

**Root Cause**: Certificate files have incorrect permissions

**Resolution**: Fix file permissions

```bash
# Check current permissions
ls -la deploy-containers/traefik/certs/

# Fix permissions (if needed)
chmod 644 deploy-containers/traefik/certs/*.crt
chmod 600 deploy-containers/traefik/certs/*.key

# Restart Traefik
ichrisbirch dev restart
```

**Prevention**: The ssl-manager script sets proper permissions automatically

### 8. Certificate File Missing

**Problem**: Traefik can't find certificate files

**Error Messages**:

```text
unable to load X509 key pair: open /etc/traefik/certs/dev.crt: no such file or directory
```

**Root Cause**: Certificate files not generated or in wrong location

**Resolution**: Generate certificates

```bash
# Check if certificates exist
ls -la deploy-containers/traefik/certs/

# Generate missing certificates
ichrisbirch ssl-manager generate dev

# Verify certificate files
ichrisbirch ssl-manager validate dev

# Restart environment
ichrisbirch dev restart
```

**Prevention**: Always run certificate generation before starting environments

## 🔧 Advanced Certificate Debugging

### OpenSSL Certificate Testing

```bash
# Test certificate with OpenSSL
openssl s_client -connect api.docker.localhost:443 -servername api.docker.localhost

# Check certificate details
openssl x509 -in deploy-containers/traefik/certs/dev.crt -text -noout

# Verify certificate-key pair match
openssl x509 -noout -modulus -in deploy-containers/traefik/certs/dev.crt | openssl md5
openssl rsa -noout -modulus -in deploy-containers/traefik/certs/dev.key | openssl md5
```

### Browser Certificate Cache

```bash
# Clear Chrome certificate cache (macOS)
# Chrome -> Settings -> Privacy and security -> Clear browsing data -> Advanced -> Cached images and files

# Clear Safari certificate cache (macOS)
# Safari -> Develop -> Empty Caches

# Clear Firefox certificate cache
# Firefox -> Settings -> Privacy & Security -> Certificates -> Clear
```

### System Certificate Store Debugging

```bash
# macOS: Check system certificate store
security find-certificate -c "mkcert" /Library/Keychains/System.keychain

# Linux: Check certificate store
ls /usr/local/share/ca-certificates/

# Windows: Check certificate store
certmgr.msc  # Run this to open Certificate Manager
```

## 🛠️ SSL Manager Tool Usage

### Generate Certificates

```bash
# Generate certificates for development (prefers mkcert)
ichrisbirch ssl-manager generate dev

# Generate certificates for all environments
ichrisbirch ssl-manager generate all

# Force OpenSSL generation (for testing)
FORCE_OPENSSL=1 ichrisbirch ssl-manager generate dev
```

### Validate Certificates

```bash
# Validate specific environment certificates
ichrisbirch ssl-manager validate dev

# Validate all environment certificates
ichrisbirch ssl-manager validate all
```

### Certificate Information

```bash
# Show detailed certificate information
ichrisbirch ssl-manager info dev

# Show certificate information for all environments
ichrisbirch ssl-manager info all
```

## 🚀 Best Practices

### Development Environment Setup

1. **Install mkcert first**: Always install mkcert before generating certificates
2. **Install CA**: Run `mkcert -install` to trust the local Certificate Authority
3. **Generate certificates**: Use `ichrisbirch ssl-manager generate dev`
4. **Verify browser trust**: Test <https://api.docker.localhost/> in browser
5. **Document for team**: Ensure all developers follow the same setup

### Certificate Management

1. **Use mkcert for development**: Avoid OpenSSL self-signed certificates
2. **Long validity periods**: mkcert certificates last 2+ years
3. **Environment-specific certificates**: Use separate certificates for dev/testing/prod
4. **Regular validation**: Use `ssl-manager validate` to check certificate health
5. **Backup certificates**: Keep certificate backups for team sharing

### Troubleshooting Workflow

1. **Check certificate existence**: `ls deploy-containers/traefik/certs/`
2. **Validate certificates**: `ichrisbirch ssl-manager validate dev`
3. **Check certificate info**: `ichrisbirch ssl-manager info dev`
4. **Test browser access**: Visit <https://api.docker.localhost/>
5. **Check Traefik logs**: `ichrisbirch dev logs traefik`
6. **Regenerate if needed**: `ichrisbirch ssl-manager generate dev`

### Security Considerations

1. **Keep CA private**: Don't share mkcert CA root key
2. **Environment isolation**: Use separate certificates for each environment
3. **Regular updates**: Update mkcert periodically
4. **Production certificates**: Use proper CA-signed certificates for production
5. **Key protection**: Protect private key files with appropriate permissions

## 🌟 mkcert Benefits Over OpenSSL

### Technical Advantages

| Feature | mkcert | OpenSSL Self-Signed |
|---------|--------|-------------------|
| Browser Trust | ✅ Trusted automatically | ❌ Requires manual trust |
| Certificate Warnings | ✅ No warnings | ❌ Security warnings |
| Subject Alternative Names | ✅ Automatic wildcard + specific | ⚠️ Manual configuration |
| Validity Period | ✅ 2+ years | ⚠️ 365 days typical |
| Cross-Platform | ✅ Works on all platforms | ⚠️ Platform-specific trust |
| Team Sharing | ✅ Same CA for all developers | ❌ Individual trust required |

### User Experience Improvements

1. **No security warnings**: Browsers trust mkcert certificates immediately
2. **Professional development**: Development environment matches production behavior
3. **Team consistency**: All developers use the same trusted certificates
4. **Faster onboarding**: New developers don't need to manually trust certificates
5. **Better testing**: Can test SSL-specific features without bypassing verification

The SSL certificate strategy using mkcert provides a professional, secure foundation for local development with excellent browser compatibility and team collaboration benefits.
