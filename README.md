# Conversational DB Copilot

Production-style full-stack structure with:

- FastAPI backend
- React + Vite frontend
- Groq for NL -> SQL planning
- PostgreSQL (Aiven-ready)
- Strict SQL safety guardrails (`SELECT`, `INSERT`, `UPDATE` only)

## Folder Structure

- `backend/` FastAPI app and services
- `frontend/` React app

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

## API Endpoints

- `GET /api/v1/health`
- `POST /api/v1/auth/login`
- `POST /api/v1/chat`

## Security Rules

The assistant will not execute:

- `DELETE`
- `DROP`
- `ALTER`
- `TRUNCATE`
- Any schema-changing operation
# text2SQL
