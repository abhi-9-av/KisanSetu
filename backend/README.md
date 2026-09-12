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

## Development authentication

The local OTP flow is deliberately not real authentication and never sends
SMS. Request an OTP, then verify with the fixed demo code `1234`:

```bash
curl -X POST http://localhost:8000/api/v1/auth/request-otp \
  -H 'content-type: application/json' -d '{"phone":"9876543210"}'
curl -X POST http://localhost:8000/api/v1/auth/verify-otp \
  -H 'content-type: application/json' -d '{"phone":"9876543210","otp":"1234"}'
```

The returned bearer token is an in-memory, short-lived local development
session. It is not a production token implementation.

With the server running, the repository smoke check can be run with
`python backend/validate_api.py`.

## Endpoints

- `GET /health`
- `GET /api/v1/health`
- `POST /api/v1/auth/request-otp`
- `POST /api/v1/auth/verify-otp`
- `GET /api/v1/farmer/profile` (Bearer session required)
- `PATCH /api/v1/farmer/profile` (Bearer session required)
- `GET /api/v1/centres?search=indore`

The database is created as `kisansetu.db` in the working directory. It is
ignored by Git and can be recreated at any time from the seed command.
