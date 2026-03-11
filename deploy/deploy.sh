#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/edenai-teacher
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"

cd "$APP_DIR"

echo "[1/6] update source"
git pull --ff-only

echo "[2/6] backend install"

if [ ! -d "$BACKEND_DIR/.venv" ]; then
  python3 -m venv "$BACKEND_DIR/.venv"
fi

source "$BACKEND_DIR/.venv/bin/activate"
pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements.txt"

echo "[3/6] backend syntax check"
python -m compileall "$BACKEND_DIR/app"

echo "[4/6] frontend build"
cd "$FRONTEND_DIR"
npm ci
npm run build

echo "[5/6] restart backend"
sudo systemctl daemon-reload
sudo systemctl restart edenai-backend
sudo systemctl --no-pager --full status edenai-backend

echo "[6/6] reload nginx"
sudo nginx -t
sudo systemctl reload nginx

echo "Deploy finished."
