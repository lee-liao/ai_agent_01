# SSL Certificate Setup

## Overview

Both frontend and backend need SSL certificates for HTTPS communication. The certificates are generated once and copied to both locations.

---

## Setup Steps

### 1. Generate SSL Certificates (Backend)

```bash
cd exercise_10/backend/sslCertificates
python create_cert.py
```

This creates:
- `cert.pem` - SSL certificate
- `key.pem` - Private key

**Included IPs:**
- localhost (127.0.0.1)
- 192.168.10.210 (LAN)
- 192.168.10.244 (LAN)
- 103.98.213.149 (WAN/Public)

---

### 2. Copy Certificates to Frontend

#### Windows (PowerShell):
```powershell
# Create frontend SSL directory
mkdir exercise_10\frontend\sslCertificates -Force

# Copy certificates
copy exercise_10\backend\sslCertificates\cert.pem exercise_10\frontend\sslCertificates\
copy exercise_10\backend\sslCertificates\key.pem exercise_10\frontend\sslCertificates\
```

#### Linux/Ubuntu:
```bash
# Create frontend SSL directory
mkdir -p exercise_10/frontend/sslCertificates

# Copy certificates
cp exercise_10/backend/sslCertificates/cert.pem exercise_10/frontend/sslCertificates/
cp exercise_10/backend/sslCertificates/key.pem exercise_10/frontend/sslCertificates/
```

---

### 3. Verify Certificates Exist

Check that both locations have the certificates:

```
exercise_10/backend/sslCertificates/
  - cert.pem
  - key.pem

exercise_10/frontend/sslCertificates/
  - cert.pem
  - key.pem
```

---

## Usage

### Backend (with SSL):
```bash
cd exercise_10/backend
uvicorn app.main:app --host 0.0.0.0 --port 8600 \
  --ssl-keyfile ./sslCertificates/key.pem \
  --ssl-certfile ./sslCertificates/cert.pem \
  --reload
```

### Frontend (with SSL):
```bash
cd exercise_10/frontend
node server.js
```

The frontend `server.js` automatically loads:
- `sslCertificates/key.pem`
- `sslCertificates/cert.pem`

---

## Docker Compose

For Docker Compose, certificates are mounted as volumes:

```yaml
# Backend
volumes:
  - ./backend/sslCertificates:/app/sslCertificates

# Frontend
volumes:
  - ./frontend/sslCertificates:/app/sslCertificates
```

Each container needs its own copy because they have separate filesystems.

---

## Troubleshooting

### "Certificate file not found" error:

**Check if certificates exist:**
```bash
# Backend
ls exercise_10/backend/sslCertificates/

# Frontend
ls exercise_10/frontend/sslCertificates/
```

**If missing, regenerate and copy:**
```bash
# 1. Generate
cd exercise_10/backend/sslCertificates
python create_cert.py

# 2. Copy to frontend (choose your OS)
# Windows:
copy *.pem ..\..\frontend\sslCertificates\

# Linux:
cp *.pem ../../frontend/sslCertificates/
```

### "Certificate not trusted" browser warning:

This is normal for self-signed certificates. Click "Advanced" → "Proceed" to accept.

---

## .gitignore

SSL certificates are excluded from git for security:

```gitignore
exercise_10/backend/sslCertificates/
exercise_10/frontend/sslCertificates/
```

Each developer must generate their own certificates locally.

---

## Quick Setup (All-in-One)

```bash
# Generate backend certificates
cd exercise_10/backend/sslCertificates
python create_cert.py

# Copy to frontend (Windows)
cd ..\..
mkdir frontend\sslCertificates -Force
copy backend\sslCertificates\*.pem frontend\sslCertificates\

# Copy to frontend (Linux)
cd ../..
mkdir -p frontend/sslCertificates
cp backend/sslCertificates/*.pem frontend/sslCertificates/

# Done! Start servers:
# Terminal 1: cd exercise_10/backend && uvicorn app.main:app --host 0.0.0.0 --port 8600 --ssl-keyfile ./sslCertificates/key.pem --ssl-certfile ./sslCertificates/cert.pem --reload
# Terminal 2: cd exercise_10/frontend && node server.js
```

