# Backend (FastAPI)

## Setup

1. Create virtual environment and activate it.
2. Install dependencies:
   pip install -r requirements.txt
3. Create `.env` from `.env.example` and fill values.
4. Run server:
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## Environment Variables

Required:

- `AIVEN_POSTGRES_URL` or `DATABASE_URL`: PostgreSQL connection string
- `GROQ_API_KEY`: Groq API key

Optional:

- `GROQ_MODEL`: Groq model id
- `APP_LOGIN_USERNAME` / `APP_LOGIN_PASSWORD`: login creds for frontend auth
- `TOKEN_TTL_MINUTES`: auth token lifetime
- `CORS_ORIGINS`: comma-separated allowed origins or `*`

RAG:

- `CHROMA_PATH`: local folder to persist embeddings
- `RAG_TOP_K`: number of schema chunks to retrieve
- `EMBEDDING_MODEL`: sentence-transformers model id
- `TRANSFORMERS_NO_TF` / `TRANSFORMERS_NO_FLAX`: keep transformers CPU-only

## API Base

- Base URL: `http://127.0.0.1:8000/api/v1`
- Health: `GET /health`
- Login: `POST /auth/login`
- Chat: `POST /chat`
