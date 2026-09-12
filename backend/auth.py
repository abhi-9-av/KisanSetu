"""Development-only OTP and bearer sessions.

This intentionally does not send SMS.  It is a small in-memory store for local
development and is not suitable for production or multiple backend processes.
"""

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

DEMO_OTP = "1234"
OTP_TTL = timedelta(minutes=5)
SESSION_TTL = timedelta(days=7)

_otps: dict[str, tuple[str, datetime]] = {}
_sessions: dict[str, tuple[str, datetime]] = {}


def issue_otp(phone: str) -> None:
    _otps[phone] = (DEMO_OTP, datetime.now(timezone.utc) + OTP_TTL)


def verify_otp(phone: str, otp: str) -> bool:
    entry = _otps.get(phone)
    if not entry:
        return False
    expected, expires_at = entry
    if datetime.now(timezone.utc) >= expires_at or otp != expected:
        return False
    _otps.pop(phone, None)
    return True


def create_session(farmer_id: str) -> str:
    token = token_urlsafe(32)
    _sessions[token] = (farmer_id, datetime.now(timezone.utc) + SESSION_TTL)
    return token


def farmer_id_for_token(token: str) -> str | None:
    entry = _sessions.get(token)
    if not entry:
        return None
    farmer_id, expires_at = entry
    if datetime.now(timezone.utc) >= expires_at:
        _sessions.pop(token, None)
        return None
    return farmer_id
