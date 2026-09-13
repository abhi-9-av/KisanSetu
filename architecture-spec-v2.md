# KisanSetu: Technical Architecture & API Specifications

This document describes the implemented code layout, database models, and API
endpoints for **KisanSetu** (SIH 2026 Problem Statement 26032). The running
FastAPI application in `backend/main.py` and the Pydantic schemas are the
authoritative API contract.

---

## 📁 Recommended Repository Layout

```
KisanSetu/
├── .github/
│   └── copilot-instructions.md       # Copilot system prompt
├── data-contract-v2.json              # Shared JSON schema specification
├── architecture-spec-v2.md            # System architecture (this file)
├── backend/                           # FastAPI Server
│   ├── main.py                        # FastAPI entrypoint & routes
│   ├── database.py                    # SQLite engine & session maker
│   ├── models.py                      # SQLAlchemy ORM models
│   ├── schemas.py                     # Pydantic schemas
│   ├── alembic/                       # Database migrations
│   └── tests/                         # Backend regression tests
├── apps/
│   ├── mobile/                        # React Native (Expo + TypeScript)
│   │   ├── App.tsx                    # Main app container
│   │   ├── app/                       # Expo Router screens
│   │   │   ├── index.tsx              # Home & Slot Booking
│   │   │   ├── queue.tsx              # Live Token & Dynamic ETA Card
│   │   │   └── payment.tsx            # Payment Tracker & Receipts
│   │   ├── components/                # Reusable UI cards
│   │   └── types/                     # TypeScript Interfaces
│   └── operator/                      # Mandi Operator Dashboard
│       └── app.py                     # Streamlit dashboard script
└── README.md
```

---

## ⚡ FastAPI REST API Endpoints

### 1. Slot Booking & Search
- `GET /api/v1/centres?search={query}`
- `GET /api/v1/slots/availability?centre_id={id}&slot_date={date}`
- `POST /api/v1/bookings/create` (Bearer)
  - Body: `{ centre_id, crop_type, quantity_quintals, slot_date, slot_start_time }`
  - Creates a capacity-checked booking and token.
- `GET /api/v1/bookings`, `GET /api/v1/bookings/{booking_id}` (Bearer)
- `POST /api/v1/bookings/{booking_id}/cancel` (Bearer)

### 2. Live Queue & ETA
- `GET /api/v1/queue/status/{booking_id}`
  - Returns: `{ token_number, status, vehicles_ahead, estimated_wait_min }`
- `POST /api/v1/operator/bookings/{booking_id}/check-in`
  - Uses the development operator access header and advances `BOOKED` → `ARRIVED` → `WAITING`.

### 3. Procurement & Weighment
- `POST /api/v1/operator/bookings/{booking_id}/weighment`
  - Uses the development operator access header and records weighment and quality status.

### 4. Payment Tracker & CM Helpline Escalation
- `GET /api/v1/farmer/payments`, `GET /api/v1/farmer/payments/{booking_id}` (Bearer)
- `GET /api/v1/farmer/bookings/{booking_id}/receipt` (Bearer)
- `PATCH /api/v1/operator/bookings/{booking_id}/payment`
  - Uses the development operator access header and enforces payment transitions.
- `POST /api/v1/operator/sentinel/payment-escalations`
  - Uses the development operator access header and records payment stalls over seven days.

---

## 💾 Database Schema (SQLAlchemy / SQLite)

- **Farmers Table:** `id`, `name`, `phone`, `aadhaar_hash`, `land_hectares`
- **Centres Table:** `id`, `name`, `district`, `max_daily_capacity`, `avg_processing_mins_per_vehicle`
- **Bookings Table:** `id`, `farmer_id`, `centre_id`, `crop_type`, `quantity_quintals`, `slot_date`, `slot_time`, `token_number`, `status` (`BOOKED`, `ARRIVED`, `WAITING`, `PROCESSING`, `COMPLETED`, `CANCELLED`)
- **Payments Table:** `id`, `booking_id`, `amount_inr`, `status` (`NOT_STARTED`, `PROCUREMENT_COMPLETED`, `PAYMENT_INITIATED`, `PROCESSING`, `PAID`), `updated_at`, `days_stalled`
