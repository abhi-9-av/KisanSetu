# 🌾 KisanSetu
> **Smart India Hackathon 2026 · Problem Statement 26032**
> **Smart Procurement & Queue Management Platform for Farmers**

KisanSetu is a prototype agricultural procurement logistics platform connecting a farmer-facing mobile app, mandi-operator dashboard, and FastAPI backend. It focuses on capacity-aware bookings, queue visibility, weighment transparency, payment tracking, complaints, notifications, and payment-stall escalation.

## Core Features
- Capacity-aware slot booking with centre capacity checks and generated tokens.
- Live queue status: token state, vehicles ahead, and estimated wait.
- Digital weighment receipt after approved procurement.
- Payment state tracking: NOT_STARTED → PROCUREMENT_COMPLETED → PAYMENT_INITIATED → PROCESSING → PAID.
- Payment-stall sentinel that records unresolved escalations after 7 days.
- Farmer complaints and notifications.
- Development operator dashboard for booking, check-in, weighment, payment and escalation workflows.

## Architecture
~~~text
React Native / Expo ─────┐
                        ├── HTTP / REST ── FastAPI Backend ── SQLite/PostgreSQL
Streamlit Operator UI ──┘
~~~

## Technology Stack
| Layer | Technology |
|---|---|
| Farmer app | React Native, Expo Router, TypeScript, NativeWind |
| Operator dashboard | Python, Streamlit, Plotly |
| Backend | FastAPI, Uvicorn, Pydantic |
| Database | SQLAlchemy, SQLite / PostgreSQL |
| Migrations | Alembic |
| CI | GitHub Actions |
| Local orchestration | Docker Compose |

## Repository Structure
~~~text
KisanSetu/
├── .github/workflows/backend.yml
├── .Github/copilot-instructions-v2.md
├── .mockups/kisansetu.html
├── apps/mobile/                 # Expo farmer app
├── apps/operator/               # Streamlit dashboard
├── backend/                     # FastAPI service
│   ├── main.py
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── seed.py
│   ├── validate_api.py
│   ├── alembic/
│   └── tests/
├── architecture-spec-v2.md
├── data-contract-v2.json
├── docker-compose.yml
└── LICENSE
~~~

## Quick Start
### Docker
~~~bash
docker compose up --build
~~~
API: http://localhost:8000  |  Swagger: http://localhost:8000/docs  |  ReDoc: http://localhost:8000/redoc

### Local backend
~~~bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
alembic -c backend/alembic.ini upgrade head
python -m backend.seed
uvicorn backend.main:app --reload --port 8000
~~~

SQLite is the default for local development. PostgreSQL is required for staging/production.

## Mobile App
~~~bash
cd apps/mobile
npm install
npm start
npm run typecheck
~~~
For a physical device, set EXPO_PUBLIC_API_URL to the LAN address of the backend before starting Expo.

The current OTP flow is development-only and does not send SMS. Development OTP: 1234.

## Operator Dashboard
~~~bash
pip install -r apps/operator/requirements.txt
streamlit run apps/operator/app.py
~~~
The dashboard is development-only and must not be exposed publicly. Operator routes use the X-Operator-Access header.

## API Overview
| Method | Endpoint | Auth |
|---|---|---|
| GET | /health | Public |
| POST | /api/v1/auth/request-otp | Public |
| POST | /api/v1/auth/verify-otp | Public |
| GET/PATCH | /api/v1/farmer/profile | Bearer |
| GET | /api/v1/centres | Public |
| GET | /api/v1/slots/availability | Public |
| POST | /api/v1/bookings/create | Bearer |
| GET | /api/v1/bookings | Bearer |
| GET | /api/v1/bookings/{id} | Bearer |
| POST | /api/v1/bookings/{id}/cancel | Bearer |
| GET | /api/v1/queue/status/{id} | Bearer |
| GET | /api/v1/farmer/payments | Bearer |
| GET | /api/v1/farmer/payments/{booking_id} | Bearer |
| GET | /api/v1/farmer/bookings/{booking_id}/receipt | Bearer |
| POST/GET | /api/v1/farmer/complaints | Bearer |
| GET | /api/v1/farmer/notifications | Bearer |
| PATCH | /api/v1/farmer/notifications/{id}/read | Bearer |
| GET | /api/v1/operator/bookings | Operator |
| GET | /api/v1/operator/complaints | Operator |
| GET | /api/v1/operator/escalations | Operator |
| GET | /api/v1/operator/notifications | Operator |
| POST | /api/v1/operator/bookings/{id}/check-in | Operator |
| POST | /api/v1/operator/bookings/{id}/weighment | Operator |
| PATCH | /api/v1/operator/bookings/{id}/payment | Operator |
| POST | /api/v1/operator/sentinel/payment-escalations | Operator |

See docs/API_REFERENCE.md for detailed endpoint behaviour and examples.

## State Machines
### Booking
~~~text
BOOKED → ARRIVED → WAITING → PROCESSING → COMPLETED
   │          │
   └──────────┴────────→ CANCELLED
~~~
### Procurement
~~~text
PENDING → APPROVED
        ↘ REJECTED
~~~
### Payment
~~~text
NOT_STARTED → PROCUREMENT_COMPLETED → PAYMENT_INITIATED → PROCESSING → PAID
~~~

## Testing
~~~bash
python -m unittest discover -s backend/tests -p 'test_*.py'
python -m compileall -q backend
python backend/validate_api.py
alembic -c backend/alembic.ini upgrade head
alembic -c backend/alembic.ini current
~~~

## Security
For staging/production use PostgreSQL, unique strong AUTH_SECRET_KEY and OPERATOR_ACCESS_TOKEN values, real authentication/RBAC, shared rate limiting, restricted CORS, and protected infrastructure credentials. Never commit .env.

## Prototype Scope
KisanSetu is an SIH prototype, not a production government procurement system. The repository currently implements development versions of authentication, centre/slot data, bookings, queue estimation, check-in, weighment, receipts, payment transitions, complaints, notifications and escalation records.

Production deployment would additionally require real identity/SMS integration, live centre and queue feeds, official payment-status integration, authenticated government grievance integration, production RBAC, distributed rate limiting, monitoring/audit infrastructure, and privacy/compliance review.

## Documentation
- architecture-spec-v2.md — technical architecture
- docs/API_REFERENCE.md — detailed API reference
- data-contract-v2.json — shared data contract
- backend/README.md — backend development
- apps/mobile/README.md — mobile development
- apps/operator/README.md — dashboard development

## Smart India Hackathon 2026
**Problem Statement:** 26032  
**Title:** Smart Procurement & Queue Management Platform for Farmers  
**Theme:** Agriculture, Foodtech & Rural Development

Built by **Team KisanSetu**.

## License
MIT License. See LICENSE.