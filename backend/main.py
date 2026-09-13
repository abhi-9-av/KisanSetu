from contextlib import asynccontextmanager
import hmac
import json
from datetime import date, datetime, timedelta
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db, init_db
from . import auth
from .models import (AcceptedStatus, Booking, Centre, Complaint, Escalation, Farmer,
                     Notification, Payment, PaymentStatus, Procurement, QueueRecord,
                     TokenStatus)
from .schemas import (
    CentreResponse,
    FarmerProfile,
    FarmerProfileUpdate,
    OtpRequest,
    OtpRequestResponse,
    OtpVerifyRequest,
    OtpVerifyResponse,
    AvailabilityResponse,
    BookingCreate,
    BookingSummary,
    CheckInResponse,
    QueueStatusResponse,
    SlotAvailability,
    ComplaintCreate, ComplaintResponse, NotificationResponse, PaymentResponse,
    PaymentTransition, WeighmentUpdate, EscalationResponse,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/api/v1/health")
def api_health() -> dict[str, str]:
    return health()


bearer = HTTPBearer(auto_error=False)


def current_farmer(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Farmer:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer session token required")
    farmer_id = auth.farmer_id_for_token(credentials.credentials)
    farmer = db.get(Farmer, farmer_id) if farmer_id else None
    if not farmer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")
    return farmer


def development_operator_access(
    access_token: str | None = Header(default=None, alias="X-Operator-Access"),
) -> bool:
    """Validate the configured operator credential without timing leaks."""
    if not access_token or not hmac.compare_digest(
        access_token, settings.operator_access_token
    ):
        raise HTTPException(status_code=401, detail="Valid local operator access is required")
    return True


@app.post("/api/v1/auth/request-otp", response_model=OtpRequestResponse)
def request_otp(payload: OtpRequest, request: Request) -> OtpRequestResponse:
    key = f"{request.client.host if request.client else 'unknown'}:{payload.phone}"
    if not auth.check_rate_limit("request", key):
        raise HTTPException(status_code=429, detail="Too many OTP requests; try again later")
    auth.issue_otp(payload.phone)
    return OtpRequestResponse(
        phone=payload.phone,
        expires_in_seconds=int(auth.OTP_TTL.total_seconds()),
        development_otp=auth.DEMO_OTP,
        message="Development OTP only; no SMS was sent.",
    )


@app.post("/api/v1/auth/verify-otp", response_model=OtpVerifyResponse)
def verify_otp(payload: OtpVerifyRequest, request: Request, db: Session = Depends(get_db)) -> OtpVerifyResponse:
    key = f"{request.client.host if request.client else 'unknown'}:{payload.phone}"
    if not auth.check_rate_limit("verify", key):
        raise HTTPException(status_code=429, detail="Too many OTP attempts; try again later")
    if not auth.verify_otp(payload.phone, payload.otp):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP")
    farmer = db.scalar(select(Farmer).where(Farmer.phone == payload.phone))
    if not farmer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer profile not found")
    return OtpVerifyResponse(access_token=auth.create_session(farmer.id), farmer=farmer)


@app.get("/api/v1/farmer/profile", response_model=FarmerProfile)
def get_farmer_profile(farmer: Farmer = Depends(current_farmer)) -> Farmer:
    return farmer


@app.patch("/api/v1/farmer/profile", response_model=FarmerProfile)
def update_farmer_profile(
    payload: FarmerProfileUpdate,
    farmer: Farmer = Depends(current_farmer),
    db: Session = Depends(get_db),
) -> Farmer:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(farmer, field, value)
    db.commit()
    db.refresh(farmer)
    return farmer


@app.get("/api/v1/centres", response_model=list[CentreResponse])
def list_centres(
    search: str | None = Query(default=None, min_length=1),
    district: str | None = Query(default=None, min_length=1),
    db: Session = Depends(get_db),
) -> list[Centre]:
    query = select(Centre).order_by(Centre.name)
    if search:
        term = f"%{search.strip()}%"
        query = query.where(Centre.name.ilike(term) | Centre.district.ilike(term))
    if district:
        query = query.where(Centre.district.ilike(district.strip()))
    return list(db.scalars(query).all())


def _slot_rows(centre: Centre, day: date, db: Session) -> list[SlotAvailability]:
    start = datetime.combine(day, datetime.min.time()).replace(hour=8)
    end = start.replace(hour=16)
    windows = 16
    capacity = max(1, centre.max_daily_capacity // windows)
    rows = db.execute(select(Booking.slot_start_time, func.count(Booking.id)).where(
        Booking.centre_id == centre.id, Booking.slot_date == day,
        Booking.token_status != TokenStatus.CANCELLED).group_by(Booking.slot_start_time)).all()
    booked = {time: count for time, count in rows}
    result = []
    cursor = start
    while cursor < end:
        finish = cursor + timedelta(minutes=30)
        key = cursor.strftime("%H:%M")
        used = int(booked.get(key, 0))
        result.append(SlotAvailability(date=day, start_time=key, end_time=finish.strftime("%H:%M"),
                                       capacity=capacity, booked=used, available=max(0, capacity - used)))
        cursor = finish
    return result


@app.get("/api/v1/slots/availability", response_model=AvailabilityResponse)
def slot_availability(centre_id: str, slot_date: date = Query(...), db: Session = Depends(get_db)):
    centre = db.get(Centre, centre_id)
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    if slot_date < date.today():
        raise HTTPException(status_code=400, detail="Slot date cannot be in the past")
    return AvailabilityResponse(centre_id=centre_id, date=slot_date, slots=_slot_rows(centre, slot_date, db))


def _booking_response(booking: Booking) -> dict:
    queue = booking.queue
    return {"booking_id": booking.id, "farmer_id": booking.farmer_id, "farmer_name": booking.farmer.name,
            "phone": booking.farmer.phone, "centre_id": booking.centre_id, "centre_name": booking.centre.name,
            "crop_type": booking.crop_type, "quantity_quintals": booking.quantity_quintals,
            "slot": {"date": booking.slot_date, "start_time": booking.slot_start_time, "end_time": booking.slot_end_time},
            "token": {"token_number": booking.token_number, "issued_at": booking.issued_at, "status": booking.token_status},
            "queue_info": {"vehicles_ahead": queue.vehicles_ahead if queue else 0,
                           "estimated_wait_min": queue.estimated_wait_min if queue else 0,
                           "last_updated": queue.last_updated if queue else booking.created_at},
            "procurement": {"weighment_kg": booking.procurement.weighment_kg if booking.procurement else None,
                            "accepted_status": booking.procurement.accepted_status if booking.procurement else "PENDING",
                            "completed_at": booking.procurement.completed_at if booking.procurement else None},
            "payment": {"status": booking.payment.status if booking.payment else "NOT_STARTED",
                        "amount_inr": booking.payment.amount_inr if booking.payment else None,
                        "initiated_at": booking.payment.initiated_at if booking.payment else None,
                        "paid_at": booking.payment.paid_at if booking.payment else None,
                        "days_stalled": booking.payment.days_stalled if booking.payment else 0}}


@app.post("/api/v1/bookings/create", response_model=BookingSummary, status_code=201)
def create_booking(payload: BookingCreate, farmer: Farmer = Depends(current_farmer), db: Session = Depends(get_db)):
    centre = db.get(Centre, payload.centre_id)
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    try:
        start = datetime.strptime(payload.slot_start_time, "%H:%M")
        finish = datetime.strptime(payload.slot_end_time, "%H:%M")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid slot time") from exc
    if finish - start != timedelta(minutes=30) or start.hour < 8 or finish.hour > 16:
        raise HTTPException(status_code=400, detail="Slot must be a 30-minute window between 08:00 and 16:00")
    if payload.slot_date < date.today():
        raise HTTPException(status_code=400, detail="Slot date cannot be in the past")
    available = next((s for s in _slot_rows(centre, payload.slot_date, db)
                      if s.start_time == payload.slot_start_time and s.end_time == payload.slot_end_time), None)
    if not available or available.available <= 0:
        raise HTTPException(status_code=409, detail="Slot is full or unavailable")
    duplicate = db.scalar(select(Booking).where(Booking.farmer_id == farmer.id, Booking.centre_id == centre.id,
        Booking.slot_date == payload.slot_date, Booking.slot_start_time == payload.slot_start_time,
        Booking.token_status != TokenStatus.CANCELLED))
    if duplicate:
        raise HTTPException(status_code=409, detail="You already have a booking for this slot")
    day_count = db.scalar(select(func.count(Booking.id)).where(Booking.centre_id == centre.id,
        Booking.slot_date == payload.slot_date, Booking.token_status != TokenStatus.CANCELLED)) or 0
    booking = Booking(id=f"BKG-{uuid4().hex[:10].upper()}", farmer_id=farmer.id, centre_id=centre.id,
        crop_type=payload.crop_type.strip(), quantity_quintals=payload.quantity_quintals,
        slot_date=payload.slot_date, slot_start_time=payload.slot_start_time, slot_end_time=payload.slot_end_time,
        token_number=f"T-{day_count + 1:03d}")
    booking.queue = QueueRecord(id=f"Q-{uuid4().hex[:10]}", vehicles_ahead=int(day_count),
                                estimated_wait_min=int(day_count) * centre.avg_processing_mins_per_vehicle)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return _booking_response(booking)


@app.get("/api/v1/bookings", response_model=list[BookingSummary])
def list_bookings(farmer: Farmer = Depends(current_farmer), db: Session = Depends(get_db)):
    bookings = db.scalars(select(Booking).where(Booking.farmer_id == farmer.id).order_by(Booking.slot_date.desc())).all()
    return [_booking_response(b) for b in bookings]


@app.get("/api/v1/bookings/{booking_id}", response_model=BookingSummary)
def get_booking(booking_id: str, farmer: Farmer = Depends(current_farmer), db: Session = Depends(get_db)):
    booking = db.scalar(select(Booking).where(Booking.id == booking_id, Booking.farmer_id == farmer.id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return _booking_response(booking)


@app.post("/api/v1/bookings/{booking_id}/cancel", response_model=BookingSummary)
def cancel_booking(booking_id: str, farmer: Farmer = Depends(current_farmer), db: Session = Depends(get_db)):
    booking = db.scalar(select(Booking).where(Booking.id == booking_id, Booking.farmer_id == farmer.id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.token_status in (TokenStatus.CANCELLED, TokenStatus.COMPLETED, TokenStatus.PROCESSING):
        raise HTTPException(status_code=409, detail=f"Booking cannot be cancelled from {booking.token_status}")
    booking.token_status = TokenStatus.CANCELLED
    db.commit()
    db.refresh(booking)
    return _booking_response(booking)


@app.get("/api/v1/queue/status/{booking_id}", response_model=QueueStatusResponse)
def queue_status(booking_id: str, farmer: Farmer = Depends(current_farmer), db: Session = Depends(get_db)):
    booking = db.scalar(select(Booking).where(Booking.id == booking_id, Booking.farmer_id == farmer.id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if not booking.queue:
        raise HTTPException(status_code=404, detail="Queue record not found")
    return QueueStatusResponse(booking_id=booking.id, token_number=booking.token_number,
        token_status=booking.token_status, vehicles_ahead=booking.queue.vehicles_ahead,
        estimated_wait_min=booking.queue.estimated_wait_min, last_updated=booking.queue.last_updated)


def _payment_response(payment: Payment) -> dict:
    return {"payment_id": payment.id, "booking_id": payment.booking_id, "status": payment.status,
            "amount_inr": payment.amount_inr, "initiated_at": payment.initiated_at,
            "paid_at": payment.paid_at, "days_stalled": payment.days_stalled}


@app.get("/api/v1/farmer/payments", response_model=list[PaymentResponse])
def farmer_payments(farmer: Farmer = Depends(current_farmer), db: Session = Depends(get_db)):
    rows = db.scalars(select(Payment).join(Booking).where(Booking.farmer_id == farmer.id)).all()
    return [_payment_response(row) for row in rows]


@app.get("/api/v1/farmer/payments/{booking_id}", response_model=PaymentResponse)
def farmer_payment(booking_id: str, farmer: Farmer = Depends(current_farmer), db: Session = Depends(get_db)):
    payment = db.scalar(select(Payment).join(Booking).where(Payment.booking_id == booking_id,
                                                              Booking.farmer_id == farmer.id))
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return _payment_response(payment)


@app.get("/api/v1/farmer/bookings/{booking_id}/receipt")
def digital_receipt(booking_id: str, farmer: Farmer = Depends(current_farmer), db: Session = Depends(get_db)):
    booking = db.scalar(select(Booking).where(Booking.id == booking_id, Booking.farmer_id == farmer.id))
    if not booking or not booking.procurement or booking.procurement.accepted_status != AcceptedStatus.APPROVED:
        raise HTTPException(status_code=404, detail="Verified weighment receipt not available")
    return {"receipt_id": f"RCT-{booking.id}", "booking_id": booking.id, "farmer_id": farmer.id,
            "centre_id": booking.centre_id, "crop_type": booking.crop_type,
            "weighment_kg": booking.procurement.weighment_kg,
            "accepted_status": booking.procurement.accepted_status,
            "completed_at": booking.procurement.completed_at, "issued_at": datetime.utcnow()}


@app.get("/api/v1/operator/bookings", response_model=list[BookingSummary])
def operator_bookings(
    centre_id: str | None = Query(default=None),
    slot_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _: bool = Depends(development_operator_access),
):
    query = select(Booking).order_by(Booking.slot_start_time, Booking.token_number)
    if centre_id:
        query = query.where(Booking.centre_id == centre_id)
    if slot_date:
        query = query.where(Booking.slot_date == slot_date)
    return [_booking_response(row) for row in db.scalars(query).all()]


@app.get("/api/v1/operator/bookings/{booking_id}", response_model=BookingSummary)
def operator_booking_detail(
    booking_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(development_operator_access),
):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return _booking_response(booking)


@app.get("/api/v1/operator/complaints", response_model=list[ComplaintResponse])
def operator_complaints(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: bool = Depends(development_operator_access),
):
    query = select(Complaint).order_by(Complaint.created_at.desc())
    if status_filter:
        query = query.where(Complaint.status == status_filter.upper())
    return list(db.scalars(query).all())


@app.get("/api/v1/operator/escalations", response_model=list[EscalationResponse])
def operator_escalations(
    include_resolved: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: bool = Depends(development_operator_access),
):
    query = select(Escalation).order_by(Escalation.created_at.desc())
    if not include_resolved:
        query = query.where(Escalation.resolved.is_(False))
    rows = db.scalars(query).all()
    result = []
    for row in rows:
        payload = json.loads(row.payload) if row.payload else {}
        result.append({"escalation_id": row.id, "payment_id": row.payment_id,
                       "booking_id": payload.get("booking_id", ""), "reason": row.reason,
                       "payload": payload, "created_at": row.created_at})
    return result


@app.get("/api/v1/operator/notifications", response_model=list[NotificationResponse])
def operator_notifications(
    unread_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: bool = Depends(development_operator_access),
):
    query = select(Notification).order_by(Notification.created_at.desc())
    if unread_only:
        query = query.where(Notification.read.is_(False))
    return list(db.scalars(query).all())


@app.post("/api/v1/operator/bookings/{booking_id}/weighment", response_model=dict)
def operator_weighment(booking_id: str, payload: WeighmentUpdate, db: Session = Depends(get_db),
                       _: bool = Depends(development_operator_access)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.token_status not in (TokenStatus.WAITING, TokenStatus.PROCESSING):
        raise HTTPException(status_code=409, detail=f"Cannot weigh from {booking.token_status}")
    if payload.accepted_status == "APPROVED" and booking.token_status == TokenStatus.WAITING:
        booking.token_status = TokenStatus.PROCESSING
    procurement = booking.procurement or Procurement(id=f"PR-{uuid4().hex[:10]}", booking_id=booking.id)
    procurement.weighment_kg = payload.weighment_kg
    procurement.accepted_status = AcceptedStatus(payload.accepted_status)
    if procurement.accepted_status in (AcceptedStatus.APPROVED, AcceptedStatus.REJECTED):
        procurement.completed_at = datetime.utcnow()
    db.add(procurement)
    db.commit()
    return {"booking_id": booking.id, "weighment_kg": procurement.weighment_kg,
            "accepted_status": procurement.accepted_status, "completed_at": procurement.completed_at}


_PAYMENT_TRANSITIONS = {
    PaymentStatus.NOT_STARTED: {PaymentStatus.PROCUREMENT_COMPLETED},
    PaymentStatus.PROCUREMENT_COMPLETED: {PaymentStatus.PAYMENT_INITIATED},
    PaymentStatus.PAYMENT_INITIATED: {PaymentStatus.PROCESSING},
    PaymentStatus.PROCESSING: {PaymentStatus.PAID},
    PaymentStatus.PAID: set(),
}


@app.patch("/api/v1/operator/bookings/{booking_id}/payment", response_model=PaymentResponse)
def operator_payment_status(booking_id: str, payload: PaymentTransition, db: Session = Depends(get_db),
                            _: bool = Depends(development_operator_access)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    payment = booking.payment or Payment(id=f"PAY-{uuid4().hex[:10]}", booking_id=booking.id,
                                        status=PaymentStatus.NOT_STARTED)
    target = PaymentStatus(payload.status)
    if target != payment.status and target not in _PAYMENT_TRANSITIONS[payment.status]:
        raise HTTPException(status_code=409, detail=f"Invalid payment transition {payment.status} -> {target}")
    if target in (PaymentStatus.PROCUREMENT_COMPLETED, PaymentStatus.PAYMENT_INITIATED) and (
        not booking.procurement or booking.procurement.accepted_status != AcceptedStatus.APPROVED):
        raise HTTPException(status_code=409, detail="Approved weighment is required")
    payment.status = target
    if payload.amount_inr is not None:
        payment.amount_inr = payload.amount_inr
    if target == PaymentStatus.PAYMENT_INITIATED and not payment.initiated_at:
        payment.initiated_at = datetime.utcnow()
    if target == PaymentStatus.PAID:
        payment.paid_at = datetime.utcnow()
        payment.days_stalled = 0
    db.add(payment)
    db.add(Notification(id=f"NTF-{uuid4().hex[:10]}", farmer_id=booking.farmer_id,
                        title="Payment status updated",
                        message=f"Your payment is now {target.value.replace('_', ' ').title()}.",
                        kind="PAYMENT"))
    db.commit()
    db.refresh(payment)
    return _payment_response(payment)


@app.post("/api/v1/farmer/complaints", response_model=ComplaintResponse, status_code=201)
def create_complaint(payload: ComplaintCreate, farmer: Farmer = Depends(current_farmer), db: Session = Depends(get_db)):
    if payload.booking_id and not db.scalar(select(Booking).where(Booking.id == payload.booking_id,
                                                                    Booking.farmer_id == farmer.id)):
        raise HTTPException(status_code=404, detail="Booking not found")
    complaint = Complaint(id=f"CMP-{uuid4().hex[:10]}", farmer_id=farmer.id, **payload.model_dump())
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


@app.get("/api/v1/farmer/complaints", response_model=list[ComplaintResponse])
def list_complaints(farmer: Farmer = Depends(current_farmer), db: Session = Depends(get_db)):
    return list(db.scalars(select(Complaint).where(Complaint.farmer_id == farmer.id)
                           .order_by(Complaint.created_at.desc())).all())


@app.get("/api/v1/farmer/notifications", response_model=list[NotificationResponse])
def list_notifications(farmer: Farmer = Depends(current_farmer), db: Session = Depends(get_db)):
    return list(db.scalars(select(Notification).where(Notification.farmer_id == farmer.id)
                           .order_by(Notification.created_at.desc())).all())


@app.patch("/api/v1/farmer/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(notification_id: str, farmer: Farmer = Depends(current_farmer),
                            db: Session = Depends(get_db)):
    notification = db.scalar(select(Notification).where(Notification.id == notification_id,
                                                         Notification.farmer_id == farmer.id))
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.read = True
    db.commit()
    db.refresh(notification)
    return notification


@app.post("/api/v1/operator/sentinel/payment-escalations", response_model=list[EscalationResponse])
def scan_payment_escalations(db: Session = Depends(get_db), _: bool = Depends(development_operator_access)):
    cutoff = datetime.utcnow() - timedelta(days=7)
    payments = db.scalars(select(Payment).where(Payment.status.in_(
        [PaymentStatus.PAYMENT_INITIATED, PaymentStatus.PROCESSING]),
        Payment.initiated_at.is_not(None), Payment.initiated_at < cutoff)).all()
    result = []
    for payment in payments:
        payment.days_stalled = max(0, (datetime.utcnow() - payment.initiated_at).days)
        existing = db.scalar(select(Escalation).where(Escalation.payment_id == payment.id,
                                                        Escalation.resolved.is_(False)))
        if existing:
            continue
        payload = {"payment_id": payment.id, "booking_id": payment.booking_id,
                   "farmer_id": payment.booking.farmer_id, "status": payment.status,
                   "amount_inr": payment.amount_inr, "days_stalled": payment.days_stalled,
                   "destination": "CM_HELPLINE"}
        escalation = Escalation(id=f"ESC-{uuid4().hex[:10]}", payment_id=payment.id,
                                reason="Payment stalled for more than 7 days",
                                payload=json.dumps(payload))
        db.add(escalation)
        result.append((escalation, payload))
    db.commit()
    return [{"escalation_id": e.id, "payment_id": e.payment_id, "booking_id": p["booking_id"],
             "reason": e.reason, "payload": p, "created_at": e.created_at} for e, p in result]


@app.post("/api/v1/operator/bookings/{booking_id}/check-in", response_model=CheckInResponse)
def operator_check_in(booking_id: str, db: Session = Depends(get_db),
                      _: bool = Depends(development_operator_access)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.token_status == TokenStatus.BOOKED:
        booking.token_status = TokenStatus.ARRIVED
    elif booking.token_status == TokenStatus.ARRIVED:
        booking.token_status = TokenStatus.WAITING
    elif booking.token_status != TokenStatus.WAITING:
        raise HTTPException(status_code=409, detail=f"Cannot check in from {booking.token_status}")
    if not booking.queue:
        booking.queue = QueueRecord(id=f"Q-{uuid4().hex[:10]}")
    active = db.scalar(select(func.count(Booking.id)).where(Booking.centre_id == booking.centre_id,
        Booking.slot_date == booking.slot_date, Booking.token_status.in_([TokenStatus.ARRIVED, TokenStatus.WAITING]),
        Booking.id != booking.id))
    booking.queue.vehicles_ahead = int(active or 0)
    booking.queue.estimated_wait_min = booking.queue.vehicles_ahead * booking.centre.avg_processing_mins_per_vehicle
    db.commit()
    db.refresh(booking)
    return CheckInResponse(booking_id=booking.id, token_status=booking.token_status,
        queue_info={"vehicles_ahead": booking.queue.vehicles_ahead, "estimated_wait_min": booking.queue.estimated_wait_min,
                    "last_updated": booking.queue.last_updated})
