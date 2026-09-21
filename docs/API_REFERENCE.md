# KisanSetu API Reference

Developer reference for the implemented FastAPI API.

Base URL: http://localhost:8000
Interactive docs: /docs
ReDoc: /redoc

## Authentication
POST /api/v1/auth/request-otp — request a development OTP. Body: {"phone":"9876543210"}.
POST /api/v1/auth/verify-otp — verify development OTP. Body: {"phone":"9876543210","otp":"1234"}. Returns a bearer session token.
Use Authorization: Bearer <session-token> for farmer endpoints.
Operator routes require X-Operator-Access. The local default is local-operator.

## Farmer endpoints
- GET /api/v1/farmer/profile
- PATCH /api/v1/farmer/profile
- GET /api/v1/centres?search=indore
- GET /api/v1/slots/availability?centre_id=C-07&slot_date=YYYY-MM-DD
- POST /api/v1/bookings/create
- GET /api/v1/bookings
- GET /api/v1/bookings/{booking_id}
- POST /api/v1/bookings/{booking_id}/cancel
- GET /api/v1/queue/status/{booking_id}
- GET /api/v1/farmer/payments
- GET /api/v1/farmer/payments/{booking_id}
- GET /api/v1/farmer/bookings/{booking_id}/receipt
- POST /api/v1/farmer/complaints
- GET /api/v1/farmer/complaints
- GET /api/v1/farmer/notifications
- PATCH /api/v1/farmer/notifications/{notification_id}/read

## Operator endpoints
- GET /api/v1/operator/bookings
- GET /api/v1/operator/bookings/{booking_id}
- GET /api/v1/operator/complaints
- GET /api/v1/operator/escalations
- GET /api/v1/operator/notifications
- POST /api/v1/operator/bookings/{booking_id}/check-in
- POST /api/v1/operator/bookings/{booking_id}/weighment
- PATCH /api/v1/operator/bookings/{booking_id}/payment
- POST /api/v1/operator/sentinel/payment-escalations

## Booking
POST /api/v1/bookings/create accepts centre, crop, quantity, date and slot information. It creates a booking, token and queue record. Duplicate active bookings and full slots return 409.

Booking states: BOOKED → ARRIVED → WAITING → PROCESSING → COMPLETED. Eligible bookings may be cancelled.

## Queue
GET /api/v1/queue/status/{booking_id} returns token number, status, vehicles ahead, estimated wait and last update.
Operator check-in advances BOOKED → ARRIVED → WAITING.

## Weighment
POST /api/v1/operator/bookings/{booking_id}/weighment records weighment_kg and accepted_status. Accepted status values are PENDING, APPROVED and REJECTED.
GET /api/v1/farmer/bookings/{booking_id}/receipt returns a verified receipt only after approved weighment.

## Payments
Payment progression is NOT_STARTED → PROCUREMENT_COMPLETED → PAYMENT_INITIATED → PROCESSING → PAID. Invalid transitions are rejected.
PATCH /api/v1/operator/bookings/{booking_id}/payment accepts status and optionally amount_inr. Approved weighment is required before procurement-completed/payment-initiated stages.

## Escalation
POST /api/v1/operator/sentinel/payment-escalations scans PAYMENT_INITIATED and PROCESSING payments older than seven days and records an escalation payload containing payment, booking, farmer, amount, stalled days and CM_HELPLINE destination.
Prototype limitation: this records the escalation; it does not submit a live government grievance.

## Errors
| Status | Meaning |
|---|---|
| 200 | Success |
| 201 | Resource created |
| 401 | Authentication failure |
| 404 | Resource not found |
| 409 | Capacity conflict, duplicate booking, or invalid state transition |
| 422 | Validation failure |

## Runtime contract
backend/schemas.py is the runtime request/response contract. data-contract-v2.json contains the shared high-level entity contract.

## Related implementation
- backend/main.py — routes and business logic
- backend/schemas.py — request/response schemas
- backend/models.py — ORM models and enums
- backend/auth.py — authentication
- backend/config.py — settings
- backend/seed.py — demo data
- backend/tests/ — tests