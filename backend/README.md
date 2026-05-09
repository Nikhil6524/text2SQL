# Backend (FastAPI)

## Setup

1. Create virtual environment and activate it.
2. Install dependencies:
   pip install -r requirements.txt
3. Create `.env` from `.env.example` and fill values.
4. Run server:
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## API Base

- Base URL: `http://127.0.0.1:8000/api/v1`
- Health: `GET /health`
- Login: `POST /auth/login`
- Chat: `POST /chat`
