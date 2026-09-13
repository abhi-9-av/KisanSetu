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

The returned bearer token is a signed, short-lived token. Set a unique
`AUTH_SECRET_KEY` (32+ random characters) outside development; tokens are
stateless and can be verified by multiple instances sharing that key.

OTP request and verification endpoints have a lightweight process-local rate
limit. This is suitable for a local deployment only; use shared storage (such
as Redis) or an API gateway rate limiter when running multiple workers or
instances. In non-development environments, configure a unique
`OPERATOR_ACCESS_TOKEN` (16+ random characters); the development default is
rejected at startup. Never commit these secrets or place them in client code.

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
- `GET /api/v1/slots/availability?centre_id=C-07&slot_date=YYYY-MM-DD`
- `POST /api/v1/bookings/create` (Bearer; creates a capacity-checked booking and token)
- `GET /api/v1/bookings`, `GET /api/v1/bookings/{id}` (Bearer)
- `POST /api/v1/bookings/{id}/cancel` (Bearer)
- `GET /api/v1/queue/status/{id}` (Bearer)
- `POST /api/v1/operator/bookings/{id}/check-in` (operator transition BOOKED → ARRIVED → WAITING)
- `POST /api/v1/operator/bookings/{id}/weighment` (weighment and accepted status)
- `PATCH /api/v1/operator/bookings/{id}/payment` (strict payment state transition)
- `GET /api/v1/farmer/payments`, `GET /api/v1/farmer/payments/{booking_id}` (Bearer)
- `GET /api/v1/farmer/bookings/{booking_id}/receipt` (Bearer; verified digital receipt)
- `POST /api/v1/farmer/complaints`, `GET /api/v1/farmer/complaints` (Bearer)
- `GET /api/v1/farmer/notifications`, `PATCH /api/v1/farmer/notifications/{id}/read` (Bearer)
- `POST /api/v1/operator/sentinel/payment-escalations` (development scan; records stalls over seven days)

Booking slots are derived as 30-minute windows from 08:00–16:00. Daily centre
capacity is distributed across those windows; duplicate active farmer bookings
and full slots return HTTP 409.

The database is created as `kisansetu.db` in the working directory. It is
ignored by Git and can be recreated at any time from the seed command.
