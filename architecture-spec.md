# KrishiPragati: Technical Architecture & API Specifications

This document defines the complete code layout, database models, and API endpoints for **KrishiPragati** (SIH 2026 Problem Statement 26032). Use this specification as a single source of truth when prompting GitHub Copilot.

---

## 📁 Recommended Repository Layout

```
krishipragati/
├── .github/
│   └── copilot-instructions.md       # Copilot system prompt
├── DATA_CONTRACT.json                 # Shared JSON schema specification
├── ARCHITECTURE.md                    # System architecture (this file)
├── backend/                           # FastAPI Server
│   ├── main.py                        # FastAPI entrypoint & routes
│   ├── database.py                    # SQLite engine & session maker
│   ├── models.py                      # SQLAlchemy ORM models
│   ├── schemas.py                     # Pydantic schemas
│   ├── queue_engine.py                # ETA & capacity calculation logic
│   └── sentinel.py                    # 7-day payment escalation daemon
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

## ⚡ FastAPI REST API Endpoints Specification

### 1. Slot Booking & Search
- `GET /api/v1/centres/search?crop={crop}&lat={lat}&lng={lng}`
  - Returns recommended procurement centres sorted by capacity & distance.
- `POST /api/v1/bookings/create`
  - Body: `{ farmer_id, centre_id, crop_type, quantity_quintals, slot_date, slot_time }`
  - Action: Creates booking, generates `token_number` (e.g., `T-018`), and returns booking record.

### 2. Live Queue & ETA
- `GET /api/v1/queue/status/{booking_id}`
  - Returns: `{ token_number, status, vehicles_ahead, estimated_wait_min }`
- `POST /api/v1/operator/checkin`
  - Body: `{ booking_id, vehicle_number }`
  - Action: Updates status to `ARRIVED` -> `WAITING`, updates queue depth.

### 3. Procurement & Weighment
- `POST /api/v1/operator/weighment`
  - Body: `{ booking_id, weight_kg, quality_grade }`
  - Action: Sets status to `PROCUREMENT_COMPLETED`, sets payment status to `PAYMENT_INITIATED`, issues digital receipt.

### 4. Payment Tracker & CM Helpline Escalation
- `GET /api/v1/payment/track/{booking_id}`
  - Returns transaction milestone timestamps and `days_stalled`.
- `POST /api/v1/sentinel/check-escalations`
  - Action: Scans database for payments pending > 7 days, posts automated webhook payload to CM Helpline API endpoint.

---

## 💾 Database Schema (SQLAlchemy / SQLite)

- **Farmers Table:** `id`, `name`, `phone`, `aadhaar_hash`, `land_hectares`
- **Centres Table:** `id`, `name`, `district`, `max_daily_capacity`, `avg_processing_mins_per_vehicle`
- **Bookings Table:** `id`, `farmer_id`, `centre_id`, `crop_type`, `quantity_quintals`, `slot_date`, `slot_time`, `token_number`, `status` (`BOOKED`, `ARRIVED`, `WAITING`, `PROCESSING`, `COMPLETED`, `CANCELLED`)
- **Payments Table:** `id`, `booking_id`, `amount_inr`, `status` (`NOT_STARTED`, `PROCUREMENT_COMPLETED`, `PAYMENT_INITIATED`, `PROCESSING`, `PAID`), `updated_at`, `days_stalled`
