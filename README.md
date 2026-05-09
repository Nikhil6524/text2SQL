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

#### Backend .env

Create `.env` from `.env.example` and fill these values:

- `AIVEN_POSTGRES_URL` or `DATABASE_URL`: PostgreSQL connection string
- `GROQ_API_KEY`: Groq API key
- `GROQ_MODEL`: Groq model id (default in example)
- `APP_LOGIN_USERNAME` / `APP_LOGIN_PASSWORD`: login creds for frontend auth
- `TOKEN_TTL_MINUTES`: auth token lifetime
- `CORS_ORIGINS`: comma-separated allowed origins or `*`

RAG settings (optional):

- `CHROMA_PATH`: local folder to persist embeddings (default `.chroma`)
- `RAG_TOP_K`: number of schema chunks to retrieve
- `EMBEDDING_MODEL`: sentence-transformers model id
- `TRANSFORMERS_NO_TF` / `TRANSFORMERS_NO_FLAX`: keep transformers CPU-only

### 2. Frontend

```bash
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

#### Frontend .env

- `VITE_API_BASE_URL`: backend base URL, default `http://127.0.0.1:8000/api/v1`

## API Endpoints

- `GET /api/v1/health`
- `POST /api/v1/auth/login`
- `POST /api/v1/chat`
- `GET /api/v1/stats/products`

## Security Rules

The assistant will not execute:

- `DELETE`
- `DROP`
- `ALTER`
- `TRUNCATE`
- Any schema-changing operation

## How it Works

- The backend fetches the database schema and uses it for safe SQL generation.
- A schema RAG index is rebuilt on backend startup and persisted under `CHROMA_PATH`.
- SQL is validated before execution; only `SELECT`, `INSERT`, and `UPDATE` are allowed.

## Common Troubleshooting

- Backend fails to start: ensure the active Python environment matches where dependencies are installed.
- Embeddings errors: confirm `sentence-transformers` and `torch` are installed in the backend venv.
- CORS issues: set `CORS_ORIGINS` to include your frontend URL.
# text2SQL
