# Production Deployment Guide

**Status:** Ready for Production  
**Architecture:** Modular (`app/main.py`)  
**Requires:** Python 3.9+, PostgreSQL (recommended) or SQLite

## Overview

This guide covers deploying MCP Server to production environments with proper security, performance, and reliability configurations.

## Pre-Deployment Checklist

- [ ] Review [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) if migrating from legacy
- [ ] Database configured (PostgreSQL recommended for production)
- [ ] API key (`MCP_API_KEY`) generated for authentication
- [ ] CORS origins configured for your domain(s)
- [ ] Rate limiting tuned for your workload
- [ ] SSL/TLS certificate obtained (for HTTPS)
- [ ] All tests pass: `pytest tests/ -v`

## Environment Variables

### Required

```bash
# API Authentication (generates new key if not set, but should be explicit)
export MCP_API_KEY="<generate-with-$(openssl rand -hex 32)>"

# Database URL
# Option 1: PostgreSQL (RECOMMENDED for production)
export DATABASE_URL="postgresql://user:password@localhost:5432/mcp_server"

# Option 2: SQLite (development/testing only)
export DATABASE_URL="sqlite:///./mcp_server.db"
```

### Recommended

```bash
# CORS - whitelist your frontend domains(s)
export MCP_CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"

# Rate limiting - adjust based on expected load
export MCP_RATE_LIMIT="200/minute"

# Logging retention - tune based on storage
export MCP_LOG_RETENTION="5000"

# GitHub integration (optional)
export MCP_GITHUB_TOKEN="your-github-personal-access-token"

# Figma integration (optional)
export MCP_FIGMA_TOKEN="your-figma-api-token"
```

### Generate API Key

```bash
# Generate 32-byte hex string
openssl rand -hex 32

# Example: 3a7f8c1e9b4d6a2c5e8f1b4d7a9c2e5f
```

## Deployment Options

### Option 1: Standalone Server (Simple)

**Use Case:** Testing, small deployments

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MCP_API_KEY="your-generated-key"
export MCP_CORS_ORIGINS="https://yourdomain.com"

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker app.main:app
```

**Performance Tuning:**
- `-w 4` - Workers (set to 2-4x CPU cores)
- Add `--worker-class uvloop.UvicornH11Worker` for better async performance
- Add `--timeout 120` for long-running operations

### Option 2: Docker (Recommended)

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/')"

# Run application
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop"]
```

**Build and Run:**
```bash
# Build image
docker build -t mcp-server:latest .

# Run container
docker run \
  -d \
  -p 8000:8000 \
  -e MCP_API_KEY="$(openssl rand -hex 32)" \
  -e DATABASE_URL="postgresql://user:pass@postgres:5432/mcp" \
  -e MCP_CORS_ORIGINS="https://yourdomain.com" \
  --name mcp-server \
  mcp-server:latest
```

### Option 3: Docker Compose (Production-Ready)

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: mcp-postgres
    environment:
      POSTGRES_USER: mcp_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: mcp_server
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mcp_user"]
      interval: 10s
      timeout: 5s
      retries: 5
    ports:
      - "5432:5432"

  mcp-server:
    build: .
    container_name: mcp-server
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      MCP_API_KEY: ${MCP_API_KEY}
      DATABASE_URL: postgresql://mcp_user:${DB_PASSWORD}@postgres:5432/mcp_server
      MCP_CORS_ORIGINS: ${MCP_CORS_ORIGINS}
      MCP_RATE_LIMIT: "200/minute"
      MCP_LOG_RETENTION: "5000"
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

volumes:
  postgres_data:
```

**.env file:**
```bash
DB_PASSWORD=your-secure-db-password
MCP_API_KEY=your-secure-api-key
MCP_CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

**Deploy:**
```bash
docker-compose up -d
```

### Option 4: Kubernetes (Enterprise)

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: your-registry/mcp-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: MCP_API_KEY
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: api-key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: database-url
        - name: MCP_CORS_ORIGINS
          value: "https://yourdomain.com"
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 500m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-server
spec:
  selector:
    app: mcp-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**Deploy to Kubernetes:**
```bash
kubectl create secret generic mcp-secrets \
  --from-literal=api-key=$(openssl rand -hex 32) \
  --from-literal=database-url="postgresql://..."

kubectl apply -f deployment.yaml
```

## Performance Optimization

### Database Indexing

For PostgreSQL, create indexes on frequently queried fields:

```sql
CREATE INDEX idx_user_username ON "user"(username);
CREATE INDEX idx_task_status ON task(status);
CREATE INDEX idx_task_assigned_to ON task(assigned_to);
CREATE INDEX idx_log_timestamp ON log(timestamp);
```

### Connection Pooling

Use pgBouncer for PostgreSQL connection pooling:

```ini
# pgbouncer.ini
[databases]
mcp_server = host=postgres port=5432 dbname=mcp_server

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

### Caching

For high-traffic deployments, add Redis caching:

```python
# In app/main.py (future enhancement)
from redis import Redis
redis_client = Redis(host='localhost', port=6379)
```

## Monitoring & Logging

### Application Logs

```bash
# View logs (Docker Compose)
docker-compose logs -f mcp-server

# View logs (Kubernetes)
kubectl logs -f deployment/mcp-server
```

### Health Checks

```bash
# Check server health
curl http://localhost:8000/

# Check logs endpoint
curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/logs

# Check state snapshot
curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/state
```

### Metrics (Future)

Prometheus metrics available at `/metrics` (when `prometheus-fastapi-instrumentator` is added).

## Backup & Recovery

### PostgreSQL Backup

```bash
# Automated daily backup
0 2 * * * pg_dump postgresql://user:pass@localhost/mcp_server | gzip > /backups/mcp_$(date +\%Y\%m\%d).sql.gz

# Restore from backup
gunzip < /backups/mcp_20260325.sql.gz | psql -U user -d mcp_server
```

### Database Migration Strategy

```bash
# Before deploying new version:
# 1. Backup database
# 2. Test on staging
# 3. Run migrations if needed (when Alembic is configured)
# 4. Deploy
```

## Security Hardening

### SSL/TLS

```bash
# Using nginx reverse proxy
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Rate Limiting

Scale based on expected traffic:

```bash
# Conservative (testing)
export MCP_RATE_LIMIT="50/minute"

# Moderate (production)
export MCP_RATE_LIMIT="200/minute"

# Aggressive (high-traffic)
export MCP_RATE_LIMIT="500/minute"
```

### API Key Rotation

```bash
# Generate new key
NEW_KEY=$(openssl rand -hex 32)

# Update environment
export MCP_API_KEY=$NEW_KEY

# Restart service
docker-compose restart mcp-server
```

## Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| `ConnectionRefusedError` | Database not running | Start PostgreSQL service |
| `401 Unauthorized` | Missing/invalid API key | Check `MCP_API_KEY` env var |
| `CORS errors` | Domain not whitelisted | Update `MCP_CORS_ORIGINS` |
| `High memory usage` | Log retention too high | Reduce `MCP_LOG_RETENTION` |
| `Slow queries` | Missing database indexes | Create indexes (see above) |

## Support & Updates

- Check logs: `docker-compose logs mcp-server`
- Test connectivity: `curl http://localhost:8000/docs`
- Review configuration: `env | grep MCP_`
- Run tests: `pytest tests/ -v`

---

**Recommendation:** Start with Docker Compose for production. Scale to Kubernetes once you have 3+ instances.
