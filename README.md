# EdenAI Teacher

EdenAI Teacher is an AI tutoring web app for programming learning.
It supports question answering with chat history and organization knowledge documents.

## Tech Stack

- Frontend: React + Vite + TypeScript
- Backend: FastAPI + SQLAlchemy
- DB: PostgreSQL (recommended for production), SQLite (local quick start)
- LLM: Groq OpenAI-compatible API

## Core Features

- Student login/register and chat Q&A
- Teacher-only admin panel
- Knowledge docs upload/list/delete/reload (`.txt/.md/.markdown`)
- User activation and role management (`student`/`teacher`)

## Knowledge Source Behavior

Knowledge is loaded from two possible sources:

- DB knowledge (`knowledge_docs` table)
- Static files (`backend/app/data/company_docs`)

Behavior is controlled by env vars:

- `KNOWLEDGE_ENABLE_DB` (default: `true`)
- `KNOWLEDGE_ENABLE_STATIC` (default: `true` in development, `false` in production)
- `KNOWLEDGE_STATIC_DIR` (optional custom directory)

Recommended for VPS production:

- `KNOWLEDGE_ENABLE_DB=true`
- `KNOWLEDGE_ENABLE_STATIC=false`

## Project Structure

- `frontend/`: SPA source and build artifacts
- `backend/app/`: API, services, models
- `backend/tools/`: utility scripts
- `deploy/`: Sakura VPS deployment templates (nginx + systemd)

## Local Development

### 1) Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2) Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`

## Environment Variables

### Backend (`backend/.env`)

Required for production:

- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `GROQ_API_KEY`
- `CORS_ORIGINS` (comma-separated)
- `TRUSTED_HOSTS` (comma-separated, e.g. `your-domain.example`)

Optional:

- `APP_NAME` 
- `ENABLE_DOCS` (default false in production) 
- `LOG_LEVEL`
- `ENV`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `ALLOW_PLAINTEXT_PASSWORD_COMPAT` (default `false`; keep `false` in production)
- `KNOWLEDGE_ENABLE_DB`
- `KNOWLEDGE_ENABLE_STATIC`
- `KNOWLEDGE_STATIC_DIR`
- `GROQ_BASE_URL`
- `GROQ_MODEL`

### Frontend (`frontend/.env`)

- `VITE_API_BASE`
  - leave empty to use same-origin (recommended with Nginx reverse proxy)
  - set explicit URL only when frontend/backend are on different origins

## Create Teacher Account

Use the script after DB is ready:

```bash
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python tools/create_teacher.py --email admin@example.com --password 123456789 --full-name Admin
```

## Deploy to Sakura VPS (Recommended Flow)

### 1) Server packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx nodejs npm git
```

### 2) App placement

```bash
sudo mkdir -p /opt/edenai-teacher
sudo chown -R $USER:$USER /opt/edenai-teacher
cd /opt/edenai-teacher
git clone <your-repo-url> .
```

### 3) Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env for production values
```

### 4) Frontend build

```bash
cd /opt/edenai-teacher/frontend
cp .env.example .env
# keep VITE_API_BASE empty for same-origin mode
npm ci
npm run build
```

### 5) systemd service

```bash
sudo cp /opt/edenai-teacher/deploy/systemd/edenai-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now edenai-backend
sudo systemctl status edenai-backend
```

### 6) Nginx

```bash
sudo cp /opt/edenai-teacher/deploy/nginx/edenai.conf /etc/nginx/sites-available/edenai.conf
sudo ln -s /etc/nginx/sites-available/edenai.conf /etc/nginx/sites-enabled/edenai.conf
sudo nginx -t
sudo systemctl reload nginx
```

### 7) TLS

Use certbot after DNS is ready.

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.example
```


### 8) Optional: Scheduled DB backup (recommended) 

```bash
sudo cp /opt/edenai-teacher/deploy/systemd/edenai-db-backup.service /etc/systemd/system/
sudo cp /opt/edenai-teacher/deploy/systemd/edenai-db-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now edenai-db-backup.timer
systemctl list-timers | grep edenai-db-backup
``` 

## Security Notes

- Always use a strong `JWT_SECRET_KEY`
- Keep `ALLOW_PLAINTEXT_PASSWORD_COMPAT=false` in production
- Restrict `CORS_ORIGINS` to your real domain(s)
- Set `TRUSTED_HOSTS` to your real domain(s), never `*` in production
- Keep `ENABLE_DOCS=false` in production unless temporary troubleshooting is needed
- Store DB and API credentials only in `.env` on server


