"""Small smoke test for the local API.

Run `uvicorn backend.main:app --port 8000` first, then:
`python backend/validate_api.py`.
"""

import json
from urllib.request import Request, urlopen

BASE_URL = "http://127.0.0.1:8000"


def call(path: str, method: str = "GET", body: dict | None = None, token: str | None = None) -> dict | list:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"content-type": "application/json"} if data else {}
    if token:
        headers["authorization"] = f"Bearer {token}"
    request = Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    with urlopen(request) as response:
        assert response.status == 200
        return json.load(response)


call("/api/v1/auth/request-otp", "POST", {"phone": "9876543210"})
session = call("/api/v1/auth/verify-otp", "POST", {"phone": "9876543210", "otp": "1234"})
token = session["access_token"]
profile = call("/api/v1/farmer/profile", token=token)
assert profile["phone"] == "9876543210"
centres = call("/api/v1/centres?search=Indore")
assert centres
print("KisanSetu API smoke validation passed")
