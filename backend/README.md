# KisanSetu backend

This is the local FastAPI and SQLite foundation for the KisanSetu app.

## Setup

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m backend.seed
uvicorn backend.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Open
`http://localhost:8000/docs` for the interactive API documentation.

## Current endpoints

- `GET /health`
- `GET /api/v1/health`

The database is created as `kisansetu.db` in the working directory. It is
ignored by Git and can be recreated at any time from the seed command.
