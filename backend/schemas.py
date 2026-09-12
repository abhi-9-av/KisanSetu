from datetime import datetime
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
