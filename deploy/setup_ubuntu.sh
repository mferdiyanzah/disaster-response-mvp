#!/bin/bash
set -e

PROJECT_DIR="/home/ferdiyanzah/Engineering/Projects/disaster-response-mvp"

echo "=== Disaster Response MVP - Ubuntu VPS Setup ==="

# Install Python if needed
if ! command -v python3 &> /dev/null; then
    sudo apt update
    sudo apt install -y python3 python3-venv python3-pip
fi

cd "$PROJECT_DIR"

# Create venv
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install deps
pip install -r requirements.txt

# Validate .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found. Copy from .env.example and fill in values."
    exit 1
fi

# Copy systemd services
sudo cp deploy/disaster-bot.service /etc/systemd/system/
sudo cp deploy/disaster-dashboard.service /etc/systemd/system/

# Reload and enable
sudo systemctl daemon-reload
sudo systemctl enable disaster-bot
sudo systemctl enable disaster-dashboard

# Start services
sudo systemctl restart disaster-bot
sudo systemctl restart disaster-dashboard

echo ""
echo "=== Setup Complete ==="
echo "Bot status:       sudo systemctl status disaster-bot"
echo "Dashboard status: sudo systemctl status disaster-dashboard"
echo ""
echo "Bot logs:         sudo journalctl -u disaster-bot -f"
echo "Dashboard logs:   sudo journalctl -u disaster-dashboard -f"
echo ""
echo "Bot port:         8000"
echo "Dashboard port:   8501"
echo ""
echo "Configure Cloudflare Zero Trust to tunnel these ports."
