"""Development OTP plus signed, stateless bearer tokens.

OTP issuance remains an in-memory development stub. Signed tokens do not depend
on process-local session state, so they can be verified by multiple instances
when they share ``AUTH_SECRET_KEY``.
"""

import base64
import binascii
import hashlib
import hmac
import json
import threading
import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque

from .config import get_settings

DEMO_OTP = "1234"
OTP_TTL = timedelta(minutes=5)
SESSION_TTL = timedelta(days=7)

_otps: dict[str, tuple[str, datetime]] = {}
_rate_lock = threading.Lock()
_rate_events: dict[tuple[str, str], deque[float]] = defaultdict(deque)


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
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": farmer_id, "iat": now, "exp": now + int(SESSION_TTL.total_seconds())}

    def encode(value: dict) -> str:
        raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    unsigned = f"{encode(header)}.{encode(payload)}"
    signature = hmac.new(get_settings().auth_secret_key.encode(), unsigned.encode(), hashlib.sha256).digest()
    return f"{unsigned}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"


def farmer_id_for_token(token: str) -> str | None:
    try:
        header_part, payload_part, signature_part = token.split(".")
        unsigned = f"{header_part}.{payload_part}"
        expected = hmac.new(
            get_settings().auth_secret_key.encode(), unsigned.encode(), hashlib.sha256
        ).digest()
        supplied = base64.urlsafe_b64decode(signature_part + "=" * (-len(signature_part) % 4))
        if not hmac.compare_digest(expected, supplied):
            return None
        payload = json.loads(base64.urlsafe_b64decode(payload_part + "=" * (-len(payload_part) % 4)))
        if not isinstance(payload, dict) or payload.get("exp", 0) <= time.time() or not isinstance(payload.get("sub"), str):
            return None
        return payload["sub"]
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError, binascii.Error):
        return None


def check_rate_limit(kind: str, key: str, limit: int | None = None) -> bool:
    """Return whether an event is allowed by the local fixed-window limiter.

    This is intentionally process-local for the lightweight deployment. A
    multi-process production deployment must move these counters to shared
    storage (for example Redis) or enforce limits at the gateway.
    """
    settings = get_settings()
    limit = limit or (settings.otp_request_limit if kind == "request" else settings.otp_verify_limit)
    now = time.monotonic()
    cutoff = now - settings.otp_rate_limit_window_seconds
    with _rate_lock:
        events = _rate_events[(kind, key)]
        while events and events[0] <= cutoff:
            events.popleft()
        if len(events) >= limit:
            return False
        events.append(now)
        return True


def reset_rate_limits() -> None:
    with _rate_lock:
        _rate_events.clear()
