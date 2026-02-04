#!/bin/bash

# MLS-GOAT Deployment Script
# This script sets up nginx, builds frontend, and starts the backend

set -e

echo "===== MLS-GOAT Deployment Setup ====="

# Configuration
PROJECT_DIR="."  # Change this to your actual path
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
NGINX_CONF="/etc/nginx/sites-available/mls-goat"
NGINX_ENABLED="/etc/nginx/sites-enabled/mls-goat"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create nginx config
sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 500M;
    client_body_timeout 300s;

    # Frontend
    location / {
        root /home/azureuser/MLS-GOAT/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        index index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8000/redoc;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }
}
EOF

# Enable site
sudo ln -sf "$NGINX_CONF" "$NGINX_ENABLED"

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
sudo systemctl enable nginx

echo -e "${YELLOW}Step 5: Creating systemd service for backend${NC}"

# Create systemd service for FastAPI
sudo tee /etc/systemd/system/mls-goat-backend.service > /dev/null <<EOF
[Unit]
Description=MLS-GOAT FastAPI Backend
After=network.target

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser/MLS-GOAT
ExecStart=/home/azureuser/MLS-GOAT/backend/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable mls-goat-backend
sudo systemctl restart mls-goat-backend

echo -e "${GREEN}===== Deployment Complete! =====${NC}"
echo ""
echo "Backend status:"
sudo systemctl status mls-goat-backend --no-pager
echo ""
echo "Nginx status:"
sudo systemctl status nginx --no-pager
echo ""
echo -e "${GREEN}Your application should now be accessible at:${NC}"
echo "  - Frontend: http://your-server-ip/"
echo "  - API Docs: http://your-server-ip/docs"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  - View backend logs: sudo journalctl -u mls-goat-backend -f"
echo "  - Restart backend: sudo systemctl restart mls-goat-backend"
echo "  - Restart nginx: sudo systemctl restart nginx"
echo "  - Check nginx config: sudo nginx -t"