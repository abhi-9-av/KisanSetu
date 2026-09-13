"""Create the current KisanSetu schema."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "farmers",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=15), nullable=False),
        sa.Column("aadhaar_hash", sa.String(length=128), nullable=True),
        sa.Column("land_hectares", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_farmers_phone", "farmers", ["phone"], unique=True)
    op.create_table(
        "centres",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("max_daily_capacity", sa.Integer(), nullable=False),
        sa.Column("avg_processing_mins_per_vehicle", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "bookings",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("farmer_id", sa.String(length=32), nullable=False),
        sa.Column("centre_id", sa.String(length=32), nullable=False),
        sa.Column("crop_type", sa.String(length=80), nullable=False),
        sa.Column("quantity_quintals", sa.Float(), nullable=False),
        sa.Column("slot_date", sa.Date(), nullable=False),
        sa.Column("slot_start_time", sa.String(length=5), nullable=False),
        sa.Column("slot_end_time", sa.String(length=5), nullable=False),
        sa.Column("token_number", sa.String(length=20), nullable=False),
        sa.Column("token_status", sa.Enum("BOOKED", "ARRIVED", "WAITING", "PROCESSING", "COMPLETED", "CANCELLED", name="tokenstatus"), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["centre_id"], ["centres.id"]),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bookings_centre_id", "bookings", ["centre_id"], unique=False)
    op.create_index("ix_bookings_farmer_id", "bookings", ["farmer_id"], unique=False)
    op.create_index("ix_bookings_token_number", "bookings", ["token_number"], unique=False)
    op.create_table(
        "queue_records",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("booking_id", sa.String(length=32), nullable=False),
        sa.Column("vehicles_ahead", sa.Integer(), nullable=False),
        sa.Column("estimated_wait_min", sa.Integer(), nullable=False),
        sa.Column("last_updated", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_queue_records_booking_id", "queue_records", ["booking_id"], unique=True)
    op.create_table(
        "procurements",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("booking_id", sa.String(length=32), nullable=False),
        sa.Column("weighment_kg", sa.Float(), nullable=True),
        sa.Column("accepted_status", sa.Enum("PENDING", "APPROVED", "REJECTED", name="acceptedstatus"), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_procurements_booking_id", "procurements", ["booking_id"], unique=True)
    op.create_table(
        "payments",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("booking_id", sa.String(length=32), nullable=False),
        sa.Column("amount_inr", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("status", sa.Enum("NOT_STARTED", "PROCUREMENT_COMPLETED", "PAYMENT_INITIATED", "PROCESSING", "PAID", name="paymentstatus"), nullable=False),
        sa.Column("initiated_at", sa.DateTime(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("days_stalled", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_booking_id", "payments", ["booking_id"], unique=True)
    op.create_table(
        "complaints",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("farmer_id", sa.String(length=32), nullable=False),
        sa.Column("booking_id", sa.String(length=32), nullable=True),
        sa.Column("issue_type", sa.String(length=80), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("OPEN", "IN_REVIEW", "RESOLVED", name="complaintstatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_complaints_booking_id", "complaints", ["booking_id"], unique=False)
    op.create_index("ix_complaints_farmer_id", "complaints", ["farmer_id"], unique=False)
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("farmer_id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_farmer_id", "notifications", ["farmer_id"], unique=False)
    op.create_table(
        "escalations",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("payment_id", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.String(length=200), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_escalations_payment_id", "escalations", ["payment_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_escalations_payment_id", table_name="escalations")
    op.drop_table("escalations")
    op.drop_index("ix_notifications_farmer_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_complaints_farmer_id", table_name="complaints")
    op.drop_index("ix_complaints_booking_id", table_name="complaints")
    op.drop_table("complaints")
    op.drop_index("ix_payments_booking_id", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_procurements_booking_id", table_name="procurements")
    op.drop_table("procurements")
    op.drop_index("ix_queue_records_booking_id", table_name="queue_records")
    op.drop_table("queue_records")
    op.drop_index("ix_bookings_token_number", table_name="bookings")
    op.drop_index("ix_bookings_farmer_id", table_name="bookings")
    op.drop_index("ix_bookings_centre_id", table_name="bookings")
    op.drop_table("bookings")
    op.drop_table("centres")
    op.drop_index("ix_farmers_phone", table_name="farmers")
    op.drop_table("farmers")
