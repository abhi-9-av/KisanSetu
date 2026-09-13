"""Smoke test for authentication, availability and booking lifecycle."""
import json
import os
from urllib.request import Request, urlopen

BASE_URL = os.getenv("KISANSETU_API_URL", "http://127.0.0.1:8000").rstrip("/")


def call(path: str, method: str = "GET", body: dict | None = None, token: str | None = None,
         operator: bool = False):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"content-type": "application/json"} if data else {}
    if token:
        headers["authorization"] = f"Bearer {token}"
    if operator:
        headers["X-Operator-Access"] = os.getenv("OPERATOR_ACCESS_TOKEN", "local-operator")
    request = Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    with urlopen(request) as response:
        assert response.status in (200, 201)
        return json.load(response)


call("/api/v1/auth/request-otp", "POST", {"phone": "9876543210"})
session = call("/api/v1/auth/verify-otp", "POST", {"phone": "9876543210", "otp": "1234"})
token = session["access_token"]
assert call("/api/v1/farmer/profile", token=token)["phone"] == "9876543210"
assert call("/api/v1/centres?search=Indore")
availability = call("/api/v1/slots/availability?centre_id=C-07&slot_date=2099-01-02")
slot = next(item for item in availability["slots"] if item["available"] > 0)
booking = call("/api/v1/bookings/create", "POST", {
    "centre_id": "C-07", "crop_type": "Wheat", "quantity_quintals": 1,
    "slot_date": "2099-01-02", "slot_start_time": slot["start_time"], "slot_end_time": slot["end_time"],
}, token)
booking_id = booking["booking_id"]
assert call("/api/v1/bookings", token=token)
assert call(f"/api/v1/bookings/{booking_id}", token=token)["booking_id"] == booking_id
assert call(f"/api/v1/queue/status/{booking_id}", token=token)["booking_id"] == booking_id
assert call(f"/api/v1/operator/bookings/{booking_id}/check-in", "POST", operator=True)["token_status"] == "ARRIVED"
assert call(f"/api/v1/operator/bookings/{booking_id}/check-in", "POST", operator=True)["token_status"] == "WAITING"
assert call(f"/api/v1/bookings/{booking_id}/cancel", "POST", token=token)["token"]["status"] == "CANCELLED"
print("KisanSetu API smoke validation passed")
