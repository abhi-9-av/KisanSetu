from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db, init_db
from . import auth
from .models import Centre, Farmer
from .schemas import (
    CentreResponse,
    FarmerProfile,
    FarmerProfileUpdate,
    OtpRequest,
    OtpRequestResponse,
    OtpVerifyRequest,
    OtpVerifyResponse,
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
