# Docker & Portainer Deployment Guide

This guide covers running the OpenSubtitles REST API using Docker and managing it with Portainer.

## Quick Start

### 1. Basic Docker Run

```bash
# Build the image
docker build -t opensubtitles-api .

# Run the container
docker run -d \
  --name opensubtitles-api \
  -p 5000:5000 \
  -e OPENSUBTITLES_USERNAME=scara78 \
  -e OPENSUBTITLES_PASSWORD=scara78 \
  -e SESSION_SECRET=your-secret-key \
  opensubtitles-api
```

### 2. Docker Compose (Recommended)

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env

# Start the services
docker-compose up -d

# View logs
docker-compose logs -f opensubtitles-api
```

### 3. Docker Compose with Portainer

```bash
# Start Portainer and API together
docker-compose -f docker-compose.portainer.yml up -d

# Access Portainer at http://localhost:9000
# Access API at http://localhost:5000
# Access Traefik dashboard at http://localhost:8080
```

## Service URLs

When using the Portainer compose file:

- **Portainer**: http://localhost:9000 or http://portainer.localhost
- **OpenSubtitles API**: http://localhost:5000 or http://api.localhost  
- **Traefik Dashboard**: http://localhost:8080 or http://traefik.localhost

## Environment Variables

Required:
- `OPENSUBTITLES_USERNAME` - Your OpenSubtitles.org username
- `OPENSUBTITLES_PASSWORD` - Your OpenSubtitles.org password
- `SESSION_SECRET` - Random secret key for Flask sessions

Optional:
- `API_PORT` - Port to run on (default: 5000)
- `API_HOST` - Host to bind to (default: 0.0.0.0)

## Portainer Setup

1. **First Time Setup**:
   ```bash
   docker-compose -f docker-compose.portainer.yml up -d portainer
   ```

2. **Access Portainer**:
   - Go to http://localhost:9000
   - Create admin user on first visit
   - Select "Docker" environment

3. **Deploy API via Portainer**:
   - Go to "Stacks" → "Add stack"
   - Name: `opensubtitles-api`
   - Copy content from `docker-compose.yml`
   - Set environment variables
   - Deploy

## Management Commands

### View Container Logs
```bash
# API logs
docker logs -f opensubtitles-api

# All services logs
docker-compose logs -f
```

### Restart Services
```bash
# Restart API only
docker restart opensubtitles-api

# Restart all services
docker-compose restart
```

### Update API
```bash
# Rebuild and restart
docker-compose up -d --build opensubtitles-api
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Health Monitoring

The API includes a health check endpoint:
- URL: `/api/v1/status`
- Docker health check runs every 30 seconds
- Portainer will show health status in containers view

## Scaling

### Multiple API Instances
```bash
# Scale to 3 API instances
docker-compose up -d --scale opensubtitles-api=3
```

### Production Considerations
- Use external Redis for caching across instances
- Configure proper logging with log rotation
- Set up monitoring with Prometheus/Grafana
- Use production WSGI server settings

## Troubleshooting

### Common Issues

1. **API not responding**:
   ```bash
   docker logs opensubtitles-api
   ```

2. **Permission errors**:
   ```bash
   # Check container user
   docker exec opensubtitles-api whoami
   ```

3. **OpenSubtitles authentication**:
   ```bash
   # Test credentials
   curl http://localhost:5000/api/v1/status
   ```

### Debug Mode
```bash
# Run with debug enabled
docker run -it --rm \
  -p 5000:5000 \
  -e FLASK_DEBUG=1 \
  -e OPENSUBTITLES_USERNAME=scara78 \
  -e OPENSUBTITLES_PASSWORD=scara78 \
  opensubtitles-api
```

## Security

### Production Security
- Change default `SESSION_SECRET`
- Use environment files for secrets
- Restrict container network access
- Enable HTTPS with proper certificates
- Regular security updates

### Network Security
```yaml
# In docker-compose.yml
networks:
  api-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## Backup

### Backup Volumes
```bash
# Backup Portainer data
docker run --rm -v portainer_data:/data -v $(pwd):/backup alpine tar czf /backup/portainer-backup.tar.gz /data

# Backup API logs
docker run --rm -v $(pwd)/logs:/data -v $(pwd):/backup alpine tar czf /backup/api-logs-backup.tar.gz /data
```

## Integration Examples

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opensubtitles-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: opensubtitles-api
  template:
    metadata:
      labels:
        app: opensubtitles-api
    spec:
      containers:
      - name: api
        image: opensubtitles-api:latest
        ports:
        - containerPort: 5000
        env:
        - name: OPENSUBTITLES_USERNAME
          valueFrom:
            secretKeyRef:
              name: opensubtitles-secrets
              key: username
```

This Docker setup provides a complete containerized solution for your OpenSubtitles API with Portainer for easy management.