from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import select

from .database import SessionLocal, init_db
from .models import (
    AcceptedStatus,
    Booking,
    Centre,
    Farmer,
    Payment,
    PaymentStatus,
    Procurement,
    QueueRecord,
    TokenStatus,
)


def seed() -> None:
    init_db()
    with SessionLocal() as db:
        if db.scalar(select(Farmer).where(Farmer.phone == "9876543210")):
            print("Demo data already exists.")
            return

        farmer = Farmer(id="F-502", name="Ramesh Kumar", phone="9876543210", land_hectares=3.5)
        centre = Centre(
            id="C-07",
            name="Krishi Upaj Mandi, Indore",
            district="Indore",
            latitude=22.7196,
            longitude=75.8577,
            max_daily_capacity=180,
            avg_processing_mins_per_vehicle=12,
        )
        booking = Booking(
            id="BKG-1001",
            farmer=farmer,
            centre=centre,
            crop_type="Soybean",
            quantity_quintals=2,
            slot_date=date(2026, 9, 15),
            slot_start_time="10:30",
            slot_end_time="11:00",
            token_number="A-125",
            token_status=TokenStatus.WAITING,
            issued_at=datetime(2026, 9, 12, 8, 2),
        )
        booking.queue = QueueRecord(id=f"Q-{uuid4().hex[:10]}", vehicles_ahead=8, estimated_wait_min=32)
        booking.procurement = Procurement(
            id=f"PR-{uuid4().hex[:10]}",
            weighment_kg=200,
            accepted_status=AcceptedStatus.APPROVED,
            completed_at=datetime(2026, 9, 12, 10, 45),
        )
        booking.payment = Payment(
            id=f"PAY-{uuid4().hex[:10]}",
            amount_inr=5680,
            status=PaymentStatus.PROCESSING,
            initiated_at=datetime(2026, 9, 12, 10, 45),
        )
        db.add(booking)
        db.commit()
        print("Seeded demo farmer, centre, booking, queue, procurement, and payment data.")


if __name__ == "__main__":
    seed()
