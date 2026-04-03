#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/edenai-teacher
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"

cd "$APP_DIR"

echo "[1/7] update source"
git pull --ff-only
git log -1 --oneline

echo "[2/7] backend install"

if [ ! -d "$BACKEND_DIR/.venv" ]; then
  python3 -m venv "$BACKEND_DIR/.venv"
fi

source "$BACKEND_DIR/.venv/bin/activate"

pip install --upgrade pip
pip install --no-cache-dir -r "$BACKEND_DIR/requirements.txt"

echo "[3/7] backend syntax check"
python -m compileall "$BACKEND_DIR/app"

echo "[4/7] frontend install"
cd "$FRONTEND_DIR"

if [ ! -d node_modules ]; then
  npm ci
fi

echo "[5/7] frontend build"
npm run build

echo "[6/7] restart backend"
sudo systemctl restart edenai

echo "[7/7] reload nginx"
sudo nginx -t
sudo systemctl reload nginx

echo "Deploy finished."