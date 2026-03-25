# Production Deployment Guide

Complete guide for running MCP Server in production environments.

## Development vs Production

| Aspect | Development | Production |
|--------|-------------|-----------|
| Server | `--reload` enabled | no reload |
| Workers | 1 (single process) | 4+ (multi-worker) |
| Logging | console output | structured JSON to file |
| Auth | optional | required (MCP_API_KEY) |
| Database | SQLite in-memory/file | PostgreSQL recommended |
| CORS | `*` (allow all) | specific origins |
| Rate Limit | 100/minute | 50-200/minute |

---

## Quick Start: Production Server

### Minimal Setup

```bash
# Set required env vars
export MCP_API_KEY="your-secret-key-here"
export MCP_CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"

# Start with multiple workers
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Production-Ready Setup

```bash
# Create .env file
cat > .env << EOF
MCP_API_KEY=your-very-secret-key-change-this
MCP_CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com,https://admin.yourdomain.com
MCP_RATE_LIMIT=150/minute
MCP_LOG_RETENTION=5000
DATABASE_URL=postgresql://user:password@db.example.com:5432/mcp_server
MCP_GITHUB_TOKEN=ghp_xxxxxxxxxxxx
MCP_FIGMA_TOKEN=figi_xxxxxxxxxxxx
EOF

# Load env and start
set -a
source .env
set +a

python -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --log-level info
```

---

## Systemd Service

For Linux servers with systemd:

**Create `/etc/systemd/system/mcp-server.service`:**

```ini
[Unit]
Description=MCP Server - Model Context Protocol
After=network.target
Requires=postgresql.service

[Service]
Type=notify
User=mcp
WorkingDirectory=/opt/mcp-server
EnvironmentFile=/opt/mcp-server/.env
ExecStart=/usr/bin/python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --access-log

Restart=always
RestartSec=10

# Security settings
PrivateTmp=true
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/mcp-server/logs

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-server
sudo systemctl start mcp-server
sudo systemctl status mcp-server
```

**View logs:**

```bash
sudo journalctl -u mcp-server -f
```

---

## Docker Deployment

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create non-root user
RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/')" || exit 1

# Run
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Build and run:**

```bash
# Build
docker build -t mcp-server:latest .

# Run with environment
docker run -d \
  --name mcp-server \
  --restart unless-stopped \
  -p 8000:8000 \
  -e MCP_API_KEY="your-secret-key" \
  -e MCP_CORS_ORIGINS="https://yourdomain.com" \
  -e DATABASE_URL="postgresql://user:pass@db:5432/mcp" \
  -v mcp-logs:/app/logs \
  mcp-server:latest

# Check status
docker logs -f mcp-server
```

**Docker Compose:**

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: mcp_server
      POSTGRES_USER: mcp
      POSTGRES_PASSWORD: secure-password-here
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mcp"]
      interval: 10s
      timeout: 5s
      retries: 5

  server:
    build: .
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      MCP_API_KEY: your-secret-key-here
      MCP_CORS_ORIGINS: https://yourdomain.com,https://app.yourdomain.com
      MCP_RATE_LIMIT: 200/minute
      MCP_LOG_RETENTION: 10000
      DATABASE_URL: postgresql://mcp:secure-password-here@db:5432/mcp_server
      MCP_GITHUB_TOKEN: ${MCP_GITHUB_TOKEN}
      MCP_FIGMA_TOKEN: ${MCP_FIGMA_TOKEN}
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

volumes:
  postgres-data:
```

**Deploy with Compose:**

```bash
docker-compose up -d
docker-compose logs -f server
```

---

## Nginx Reverse Proxy

Recommended setup with SSL/TLS:

**`/etc/nginx/sites-available/mcp-server`:**

```nginx
upstream mcp_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain application/json;
    gzip_min_length 1000;

    # Proxy settings
    location / {
        proxy_pass http://mcp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Rate limiting (backup to app-level)
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;
}
```

**Enable:**

```bash
sudo ln -s /etc/nginx/sites-available/mcp-server /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Database Setup

### SQLite (Development/Small Scale)

```bash
# Automatic - just run the server
# Database created at: ./mcp_server.db
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### PostgreSQL (Production)

**1. Create database:**

```bash
# On PostgreSQL server
psql -U postgres -c "CREATE DATABASE mcp_server;"
psql -U postgres -c "CREATE USER mcp WITH PASSWORD 'secure-password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE mcp_server TO mcp;"
```

**2. Set environment variable:**

```bash
export DATABASE_URL="postgresql://mcp:secure-password@localhost:5432/mcp_server"
```

**3. Start server (tables auto-created):**

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Monitoring

### Health Check

```bash
# Built-in health endpoint
curl http://localhost:8000/

# Response
{
  "version": "1.0.0",
  "available_versions": ["v1", "v2"],
  "status": "running"
}
```

### Metrics

View structured logs from the API:

```bash
# Get recent logs
curl -X GET "http://localhost:8000/api/v1/logs?limit=10" \
  -H "X-API-Key: your-secret-key"
```

### Logging

Configure structured logging output:

```bash
# View logs in machine-readable format
python -m uvicorn app.main:app --log-level debug 2>&1 | tee server.log

# Parse JSON logs in monitoring tools
# Splunk, DataDog, CloudWatch, Stackdriver all support ingestion
```

---

## Performance Tuning

### Worker Configuration

```bash
# Recommended: 2-4 workers per CPU core
# Example: 4-core machine = 8-16 workers

# High concurrency
python -m uvicorn app.main:app --workers 16 --loop uvloop

# Load testing
ab -n 1000 -c 100 http://localhost:8000/
```

### Connection Pooling

PostgreSQL connection pool settings (recommended for production):

```bash
# Use pgBouncer for connection pooling
# min_pool_size: 5
# max_pool_size: 20
```

---

## Security Checklist

- [ ] Set strong `MCP_API_KEY` (minimum 32 characters, random)
- [ ] Enable HTTPS/TLS (via Nginx or load balancer)
- [ ] Restrict `MCP_CORS_ORIGINS` to known domains
- [ ] Use PostgreSQL instead of SQLite
- [ ] Run as non-root user
- [ ] Enable firewall rules (only allow 8000 from Nginx)
- [ ] Rotate API keys periodically
- [ ] Monitor logs for suspicious activity
- [ ] Set up rate limiting (configured via `MCP_RATE_LIMIT`)
- [ ] Enable structured logging for audit trails

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill it or use different port
python -m uvicorn app.main:app --port 8001
```

### High Memory Usage

```bash
# Reduce workers if under-utilized
python -m uvicorn app.main:app --workers 2

# Check for memory leaks in logs
python -m uvicorn app.main:app --log-level debug
```

### Database Connection Errors

```bash
# Test PostgreSQL connection
psql -h db.example.com -U mcp -d mcp_server

# Verify DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql://user:password@host:5432/database
```

### SSL Certificate Issues

```bash
# Check certificate expiry
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -text -noout | grep -A 2 "Validity"

# Renew with Let's Encrypt
sudo certbot renew --dry-run
```

---

**Last Updated:** March 2026
