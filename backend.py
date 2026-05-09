# Deprecated entrypoint
# Use `backend/run.py` or `uvicorn app.main:app` from the `backend` directory.

import sys
from pathlib import Path

import uvicorn


if __name__ == "__main__":
    backend_path = Path(__file__).resolve().parent / "backend"
    sys.path.insert(0, str(backend_path))
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
