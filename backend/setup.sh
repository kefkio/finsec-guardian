#!/usr/bin/env bash
# setup.sh — One-shot backend setup script
# Run from the backend/ directory: bash setup.sh

set -euo pipefail

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Installing solc 0.8.20 via solc-select..."
solc-select install 0.8.20
solc-select use 0.8.20

echo "==> Running Django migrations..."
python manage.py migrate

echo ""
echo "Backend is ready. Start the server with:"
echo "  python manage.py runserver 0.0.0.0:8000"
