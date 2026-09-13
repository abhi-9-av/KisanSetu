# 🌾 KisanSetu
> **SIH 2026 Problem Statement ID:** 26032  
> **Title:** Smart Procurement & Queue Management Platform for Farmers  
> **Theme:** Agriculture, Foodtech & Rural Development  

---

## 📌 Executive Summary

**KisanSetu** is an intelligent agricultural logistics and queue-coordination platform designed to eliminate massive physical delays, traffic jams, and administrative uncertainty at government procurement centers (*mandis*).

While existing state platforms (such as *e-Uparjan*) handle basic digital registration and static appointment scheduling, farmers still face multi-day physical waiting queues, idling fuel costs, and payment delays. **KisanSetu** bridges this physical "black box" gap by introducing **real-time capacity-aware slot recommendations**, **live physical queue tracking with dynamic ETAs**, and an **automated 7-day payment escalation sentinel** that directly routes unresolved payout stalls to the state **CM Helpline**.

---

## ⚡ 5 Core Power Features

1. **📅 Capacity-Aware Slot Booking:** Recommends optimized booking windows based on live center loads, travel distances, and historical congestion to prevent mandi overcrowding.
2. **🎟️ Live Queue Tracking & Dynamic ETA:** Replaces physical waiting hours with a digital token screen that updates remaining vehicles and wait times in real time.
3. **⚖️ On-Site Weight Transparency:** Sends instant digital receipts to the farmer's device as soon as crop weight is verified at the gate, preventing fraud.
4. **💸 End-to-End Payment Tracking:** Tracks the complete lifecycle of crop payouts through verified state milestones (`NOT_STARTED` → `PROCUREMENT_COMPLETED` → `PAYMENT_INITIATED` → `PROCESSING` → `PAID`).
5. **🚨 Automated CM Helpline Escalation:** An asynchronous sentinel daemon automatically packages audit logs and triggers an official grievance to the state **CM Helpline** if a payment remains stalled for over 7 days.

---

## 🛠️ System Architecture & Tech Stack

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                            CLIENT LAYER                                 │
 │  ┌───────────────────────────┐         ┌─────────────────────────────┐  │
 │  │   Farmer Mobile App       │         │   Mandi Operator Dashboard  │  │
 │  │   (React Native / Expo)   │         │     (Python Streamlit)      │  │
 │  └─────────────┬─────────────┘         └──────────────┬──────────────┘  │
 └────────────────┼──────────────────────────────────────┼─────────────────┘
                  │               HTTP / REST            │
 ┌────────────────┴──────────────────────────────────────┴─────────────────┐
 │                            BACKEND LAYER                                │
 │  ┌───────────────────────────────────────────────────────────────────┐  │
 │  │                   FastAPI Core REST Engine                        │  │
 │  │      • Capacity Scheduler     • Dynamic ETA Queue Engine          │  │
 │  │      • State Machine Manager  • Automated Sentinel Daemon         │  │
 │  └───────────────────────────────────┬───────────────────────────────┘  │
 └──────────────────────────────────────┼──────────────────────────────────┘
                                        │
 ┌──────────────────────────────────────┴──────────────────────────────────┐
 │                           DATA & INTEGRATION                            │
 │  ┌───────────────────────────┐         ┌─────────────────────────────┐  │
 │  │      SQLite Database      │         │   State CM Helpline Webhook │  │
 │  │    (Relational Storage)   │         │   (Automated Escalations)   │  │
 │  └───────────────────────────┘         └─────────────────────────────┘  │
 └─────────────────────────────────────────────────────────────────────────┘
```

* **Mobile App (Farmer Portal):** React Native (Expo), TypeScript, NativeWind / Tailwind CSS, React Hooks.
* **Operator Dashboard:** Python Streamlit, Plotly Analytics.
* **Backend Engine:** FastAPI (Python), Uvicorn, SQLAlchemy, SQLite.
* **Integrations:** RESTful Webhooks, JSON Data Contracts.

---

## 📂 Repository Structure

```
.
├── .github/
│   └── workflows/backend.yml      # Backend CI checks
├── apps/
│   ├── mobile/                    # React Native (Expo) Farmer App
│   └── operator/                  # Streamlit Mandi Operator Dashboard
├── backend/
│   ├── main.py                    # FastAPI application entrypoint
│   ├── database.py                # SQLAlchemy connection and sessions
│   ├── alembic/                   # Database migrations
│   └── tests/                     # Backend regression tests
├── data-contract-v2.json          # Canonical JSON schema for all team entities
├── architecture-spec-v2.md        # System specifications and API documentation
└── README.md                      # Project documentation
```

---

## 🚀 Quickstart Guide

### 1. Backend Server (FastAPI)
```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate  # On Windows: backend\.venv\Scripts\activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
alembic -c backend/alembic.ini upgrade head
python -m backend.seed
uvicorn backend.main:app --reload --port 8000
```
*API documentation will be available at `http://localhost:8000/docs`.*

For a PostgreSQL-backed deployment, use the checked-in Alembic migrations:

```bash
alembic -c backend/alembic.ini upgrade head
```

`DATABASE_URL` accepts `sqlite:///...` for development and
`postgresql+psycopg://user:password@host:5432/kisansetu` for staging/production.
Non-development environments reject SQLite and require strong,
non-default `AUTH_SECRET_KEY` and `OPERATOR_ACCESS_TOKEN` values. Copy
`backend/.env.example`; never commit secrets.

Run the complete local stack with Docker:

```bash
docker compose up --build
```

The API is then available at `http://localhost:8000`; stop it with
`docker compose down`.

### 2. Mandi Operator Dashboard (Streamlit)
```bash
cd apps/operator
pip install streamlit requests
streamlit run app.py
```

### 3. Farmer Mobile App (React Native / Expo)
```bash
cd apps/mobile
npm install
npx expo start
```
*Scan the generated QR code using the **Expo Go** app on iOS/Android.*

---

## 📊 Competitive Matrix

| Feature | Existing Portals (e.g. e-Uparjan) | CM Helpline | KisanSetu |
| :--- | :---: | :---: | :---: |
| Slot Booking | Static | ❌ | **Capacity-Aware & Dynamic** |
| Queue Visibility | Black Box (None) | ❌ | **Live Token & ETA Tracking** |
| Gate Verification | Manual / Paper | ❌ | **Instant Digital Receipt** |
| Grievance Handling | Manual Filing | Manual Filing | **Automated Sentinel Trigger** |

---

## 🏆 Smart India Hackathon 2026
Built with ❤️ by **Team KisanSetu**.  
*Empowering Indian farmers through transparent, predictable, and stress-free procurement logistics.*
