from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db, init_db
from . import auth
from .models import Booking, Centre, Farmer, QueueRecord, TokenStatus
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


@app.post("/api/v1/auth/request-otp", response_model=OtpRequestResponse)
def request_otp(payload: OtpRequest) -> OtpRequestResponse:
    auth.issue_otp(payload.phone)
    return OtpRequestResponse(
        phone=payload.phone,
        expires_in_seconds=int(auth.OTP_TTL.total_seconds()),
        development_otp=auth.DEMO_OTP,
        message="Development OTP only; no SMS was sent.",
    )


@app.post("/api/v1/auth/verify-otp", response_model=OtpVerifyResponse)
def verify_otp(payload: OtpVerifyRequest, db: Session = Depends(get_db)) -> OtpVerifyResponse:
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
            "procurement": {"weighment_kg": None, "accepted_status": "PENDING", "completed_at": None},
            "payment": {"status": "NOT_STARTED", "amount_inr": None, "initiated_at": None, "paid_at": None, "days_stalled": 0}}


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


@app.post("/api/v1/operator/bookings/{booking_id}/check-in", response_model=CheckInResponse)
def operator_check_in(booking_id: str, db: Session = Depends(get_db)):
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
