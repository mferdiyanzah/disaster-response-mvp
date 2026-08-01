#!/bin/bash
set -e

cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# Load env (parse manually to handle special chars)
if [ -f .env ]; then
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        # Remove leading/trailing whitespace from key
        key=$(echo "$key" | xargs)
        # Export if key is valid
        [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] && export "$key=$value"
    done < .env
fi

PORT=${PORT:-8000}
STREAMLIT_PORT=${STREAMLIT_PORT:-8501}

echo "=== Disaster Response MVP - Production ==="
echo "Bot port: $PORT"
echo "Dashboard port: $STREAMLIT_PORT"

# Create and activate venv
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

# Install deps
pip install -r requirements.txt --quiet

# Validate config
python -c "from bot import config; config.validate_config(); print('Config OK')"

# Create logs dir
mkdir -p logs

# Kill existing processes on these ports
fuser -k $PORT/tcp 2>/dev/null || true
fuser -k $STREAMLIT_PORT/tcp 2>/dev/null || true

echo "Starting Bot (webhook mode) on port $PORT..."
python -m bot.main_production >> logs/bot.log 2>&1 &
BOT_PID=$!
echo "Bot PID: $BOT_PID"

echo "Starting Dashboard on port $STREAMLIT_PORT..."
streamlit run dashboard/app.py \
    --server.port=$STREAMLIT_PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    >> logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "Dashboard PID: $DASHBOARD_PID"

echo ""
echo "=== Services Started ==="
echo "Bot: http://localhost:$PORT"
echo "Dashboard: http://localhost:$STREAMLIT_PORT"
echo ""
echo "Logs: $PROJECT_ROOT/logs/"
echo "Stop: kill $BOT_PID $DASHBOARD_PID"

# Wait for both
wait
