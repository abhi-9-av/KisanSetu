from datetime import date, datetime
from enum import StrEnum
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class TokenStatus(StrEnum):
    BOOKED = "BOOKED"
    ARRIVED = "ARRIVED"
    WAITING = "WAITING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PaymentStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    PROCUREMENT_COMPLETED = "PROCUREMENT_COMPLETED"
    PAYMENT_INITIATED = "PAYMENT_INITIATED"
    PROCESSING = "PROCESSING"
    PAID = "PAID"


class AcceptedStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ComplaintStatus(StrEnum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"


class Farmer(Base):
    __tablename__ = "farmers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    aadhaar_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    land_hectares: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="farmer")


class Centre(Base):
    __tablename__ = "centres"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    district: Mapped[str] = mapped_column(String(100))
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_daily_capacity: Mapped[int] = mapped_column(Integer)
    avg_processing_mins_per_vehicle: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="centre")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(ForeignKey("farmers.id"), index=True)
    centre_id: Mapped[str] = mapped_column(ForeignKey("centres.id"), index=True)
    crop_type: Mapped[str] = mapped_column(String(80))
    quantity_quintals: Mapped[float] = mapped_column(Float)
    slot_date: Mapped[date] = mapped_column(Date)
    slot_start_time: Mapped[str] = mapped_column(String(5))
    slot_end_time: Mapped[str] = mapped_column(String(5))
    token_number: Mapped[str] = mapped_column(String(20), index=True)
    token_status: Mapped[TokenStatus] = mapped_column(SqlEnum(TokenStatus), default=TokenStatus.BOOKED)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    farmer: Mapped[Farmer] = relationship(back_populates="bookings")
    centre: Mapped[Centre] = relationship(back_populates="bookings")
    queue: Mapped[Optional["QueueRecord"]] = relationship(back_populates="booking", uselist=False)
    procurement: Mapped[Optional["Procurement"]] = relationship(back_populates="booking", uselist=False)
    payment: Mapped[Optional["Payment"]] = relationship(back_populates="booking", uselist=False)
    complaints: Mapped[list["Complaint"]] = relationship(back_populates="booking")


class QueueRecord(Base):
    __tablename__ = "queue_records"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), unique=True, index=True)
    vehicles_ahead: Mapped[int] = mapped_column(Integer, default=0)
    estimated_wait_min: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    booking: Mapped[Booking] = relationship(back_populates="queue")


class Procurement(Base):
    __tablename__ = "procurements"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), unique=True, index=True)
    weighment_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    accepted_status: Mapped[AcceptedStatus] = mapped_column(SqlEnum(AcceptedStatus), default=AcceptedStatus.PENDING)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    booking: Mapped[Booking] = relationship(back_populates="procurement")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id"), unique=True, index=True)
    amount_inr: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(SqlEnum(PaymentStatus), default=PaymentStatus.NOT_STARTED)
    initiated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    days_stalled: Mapped[int] = mapped_column(Integer, default=0)

    booking: Mapped[Booking] = relationship(back_populates="payment")


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(ForeignKey("farmers.id"), index=True)
    booking_id: Mapped[Optional[str]] = mapped_column(ForeignKey("bookings.id"), nullable=True, index=True)
    issue_type: Mapped[str] = mapped_column(String(80))
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ComplaintStatus] = mapped_column(SqlEnum(ComplaintStatus), default=ComplaintStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    booking: Mapped[Optional[Booking]] = relationship(back_populates="complaints")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(ForeignKey("farmers.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    message: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(40), default="GENERAL")
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id"), index=True)
    reason: Mapped[str] = mapped_column(String(200))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
