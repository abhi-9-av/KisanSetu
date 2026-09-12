# GitHub Copilot System Instructions: KisanSetu (SIH 2026 PS 26032)

> **Context for GitHub Copilot:** You are assisting in building **KisanSetu** (KisanSetu), an intelligent agricultural procurement and queue management platform for Smart India Hackathon 2026 (Problem Statement 26032). Do NOT hallucinate tech stacks, state names, or JSON field names outside of this specification.

---

## 1. Core System Architecture & Tech Stack

| Module | Directory | Technology Stack | Key Responsibilities |
| :--- | :--- | :--- | :--- |
| **Farmer Mobile App** | `/apps/mobile` | React Native (Expo), TypeScript, NativeWind (Tailwind), React Hooks, Expo Router | Capacity-aware booking, live token card, dynamic ETA countdown, digital weighment receipt, payment tracker. |
| **Operator Dashboard** | `/apps/operator` | Python, Streamlit, Plotly / Altair | Vehicle check-in at mandi gate, call next token, record crop weight, update procurement status. |
| **Backend & Core Engine**| `/backend` | Python 3.11+, FastAPI, Uvicorn, SQLite, SQLAlchemy ORM | REST APIs, queue wait-time calculator, state-machine validator, 7-day CM Helpline escalation sentinel. |

---

## 2. Enforced Data Contracts (Do Not Alter Field Names)

Copilot must ALWAYS stick strictly to these field names and data types across Mobile, Streamlit, and FastAPI:

```json
{
  "booking_id": "string (e.g. BKG-1001)",
  "farmer_id": "string (e.g. F-502)",
  "farmer_name": "string",
  "phone": "string",
  "centre_id": "string (e.g. C-07)",
  "centre_name": "string",
  "crop_type": "string (e.g. Wheat / Paddy)",
  "quantity_quintals": "number",
  "slot": {
    "date": "YYYY-MM-DD",
    "start_time": "HH:MM",
    "end_time": "HH:MM"
  },
  "token": {
    "token_number": "string (e.g. T-018)",
    "issued_at": "ISO-Timestamp",
    "status": "BOOKED | ARRIVED | WAITING | PROCESSING | COMPLETED | CANCELLED"
  },
  "queue_info": {
    "vehicles_ahead": "integer",
    "estimated_wait_min": "integer",
    "last_updated": "ISO-Timestamp"
  },
  "procurement": {
    "weighment_kg": "number | null",
    "accepted_status": "PENDING | APPROVED | REJECTED",
    "completed_at": "ISO-Timestamp | null"
  },
  "payment": {
    "status": "NOT_STARTED | PROCUREMENT_COMPLETED | PAYMENT_INITIATED | PROCESSING | PAID",
    "amount_inr": "number | null",
    "initiated_at": "ISO-Timestamp | null",
    "paid_at": "ISO-Timestamp | null",
    "days_stalled": "integer"
  }
}
```

---

## 3. Strict State Machine Rules

1. **Token Status Transitions:**
   `BOOKED` → `ARRIVED` (when checked in at mandi) → `WAITING` (in queue) → `PROCESSING` (at weighbridge) → `COMPLETED`
2. **Payment Status Transitions:**
   `NOT_STARTED` → `PROCUREMENT_COMPLETED` → `PAYMENT_INITIATED` → `PROCESSING` → `PAID`
3. **Automated CM Helpline Escalation Sentinel:**
   If `payment.status` == `"PROCESSING"` or `"PAYMENT_INITIATED"` AND `payment.days_stalled` > 7:
   - Trigger automated webhook payload to CM Helpline API:
     ```json
     {
       "escalation_id": "ESC-9082",
       "booking_id": "BKG-1001",
       "farmer_id": "F-502",
       "centre_id": "C-07",
       "issue": "Payment delayed beyond 7-day SLA",
       "days_pending": 8,
       "auto_escalated_by": "KisanSetu_Sentinel_Daemon"
     }
     ```

---

## 4. Coding Rules & Constraints for Copilot

- **No Outer Heavy Dependencies:** Use Expo standard libraries for React Native, FastAPI built-ins, and standard Streamlit widgets.
- **TypeScript Strictness:** Always define interfaces for API responses using `interface BookingData { ... }`. Do NOT use `any`.
- **React Hooks Rule:** In mobile views, manage live token polling using `useState` and `useEffect` with a 10-second interval timer.
- **Backend Architecture:** Keep FastAPI routes clean in `/backend/routes/` and database models in `/backend/models.py`.
- **Fast Local Execution:** Use SQLite (`sqlite:///./krishipragati.db`) for zero-config local execution.
