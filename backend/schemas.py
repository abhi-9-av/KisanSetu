from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OtpRequest(BaseModel):
    phone: str = Field(pattern=r"^\d{10}$")


class OtpRequestResponse(BaseModel):
    phone: str
    expires_in_seconds: int
    development_otp: str
    message: str


class OtpVerifyRequest(BaseModel):
    phone: str = Field(pattern=r"^\d{10}$")
    otp: str = Field(min_length=4, max_length=4, pattern=r"^\d{4}$")


class FarmerProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    phone: str
    aadhaar_hash: Optional[str] = None
    land_hectares: Optional[float] = None
    created_at: datetime


class OtpVerifyResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    farmer: FarmerProfile


class FarmerProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    land_hectares: Optional[float] = Field(default=None, ge=0)


class CentreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    district: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    max_daily_capacity: int
    avg_processing_mins_per_vehicle: int
    created_at: datetime


class SlotAvailability(BaseModel):
    date: date
    start_time: str
    end_time: str
    capacity: int
    booked: int
    available: int


class AvailabilityResponse(BaseModel):
    centre_id: str
    date: date
    slots: list[SlotAvailability]


class BookingCreate(BaseModel):
    centre_id: str
    crop_type: str = Field(min_length=1, max_length=80)
    quantity_quintals: float = Field(gt=0)
    slot_date: date
    slot_start_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    slot_end_time: str = Field(pattern=r"^\d{2}:\d{2}$")


class BookingSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    booking_id: str
    farmer_id: str
    farmer_name: str
    phone: str
    centre_id: str
    centre_name: str
    crop_type: str
    quantity_quintals: float
    slot: dict
    token: dict
    queue_info: dict
    procurement: dict
    payment: dict


class QueueStatusResponse(BaseModel):
    booking_id: str
    token_number: str
    token_status: str
    vehicles_ahead: int
    estimated_wait_min: int
    last_updated: datetime


class CheckInResponse(BaseModel):
    booking_id: str
    token_status: str
    queue_info: dict
