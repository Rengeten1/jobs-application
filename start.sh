#!/bin/bash

# AutoJobber Raspberry Pi 5 Installer & Starter Script

# Exit immediately if a command exits with a non-zero status
set -e

# Navigate to the directory where this script is located
cd "$(dirname "$0")"

echo "=========================================="
echo "🚀 AutoJobber RPi 5 Startup Sequence"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 could not be found. Please install python3 and python3-venv."
    exit 1
fi

# 1. Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "⚙️  Virtual environment not found. Creating one now..."
    python3 -m venv venv
    echo "✅ Virtual environment created."
fi

# 2. Activate venv
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# 3. Install dependencies
echo "📦 Checking and installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install Playwright browsers
echo "🌐 Ensuring Playwright Chromium browser is installed..."
# We install just chromium to save space and ensure compatibility on ARM architecture
playwright install chromium

# 5. Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating a template..."
    echo "GITHUB_API_KEY=your_github_api_key_here" > .env
    echo "Please ensure you add your real token to the .env file!"
fi

# 6. Start the server
echo "=========================================="
echo "✅ Setup Complete. Starting AutoJobber..."
echo "=========================================="
echo "Access your dashboard from your Tailscale network at:"

# Try to get the IP address to print a helpful link
if command -v hostname &> /dev/null; then
    IP_ADDR=$(hostname -I | awk '{print $1}')
    echo "➡️  http://$IP_ADDR:8001"
fi
echo "➡️  http://localhost:8001"
echo "Press CTRL+C to stop."

# Run Uvicorn bound to 0.0.0.0 so it can be accessed remotely via Tailscale
uvicorn app.main:app --host 0.0.0.0 --port 8001
