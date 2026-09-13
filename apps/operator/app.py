"""KisanSetu local operator console.

This intentionally uses the development-only operator header; it is not an
authentication implementation and must never be exposed as a production app.
"""

from datetime import date
import os
from typing import Any

import requests
import streamlit as st


st.set_page_config(page_title="KisanSetu Operator", page_icon="🌾", layout="wide")
st.markdown(
    """<style>
    .block-container {padding-top: 2rem; max-width: 1400px}
    [data-testid="stMetricValue"] {color: #157347}
    </style>""",
    unsafe_allow_html=True,
)


def api_call(method: str, path: str, **kwargs: Any) -> Any:
    headers = {"X-Operator-Access": st.session_state.operator_token}
    try:
        response = requests.request(
            method, f"{st.session_state.api_url.rstrip('/')}{path}",
            headers=headers, timeout=8, **kwargs,
        )
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise RuntimeError(f"{response.status_code}: {detail}")
        return response.json()
    except requests.RequestException as exc:
        raise RuntimeError(f"Could not reach API: {exc}") from exc


def load(path: str, **kwargs: Any) -> Any | None:
    with st.spinner("Loading…"):
        try:
            return api_call("GET", path, **kwargs)
        except RuntimeError as exc:
            st.error(str(exc))
            return None


def action(method: str, path: str, **kwargs: Any) -> bool:
    try:
        api_call(method, path, **kwargs)
        st.success("Saved")
        st.rerun()
    except RuntimeError as exc:
        st.error(str(exc))
    return False


if "api_url" not in st.session_state:
    st.session_state.api_url = os.getenv("API_URL", "http://localhost:8000")
if "operator_token" not in st.session_state:
    st.session_state.operator_token = os.getenv("OPERATOR_ACCESS_TOKEN", "local-operator")

with st.sidebar:
    st.title("🌾 KisanSetu")
    st.caption("Local development operator console")
    st.session_state.api_url = st.text_input("API URL", st.session_state.api_url)
    st.session_state.operator_token = st.text_input(
        "Local operator access", st.session_state.operator_token, type="password",
    )
    st.warning("Development access only. Do not use in production.")
    if st.button("Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.title("Mandi operations")
st.caption("Live booking desk, procurement workflow, payments, and escalations")

centres = load("/api/v1/centres") or []
centre_options = {f"{item['name']} · {item['district']}": item["id"] for item in centres}
left, right = st.columns([2, 1])
with left:
    selected_label = st.selectbox("Centre", list(centre_options) or ["No centres available"])
with right:
    selected_date = st.date_input("Booking date", value=date.today())
centre_id = centre_options.get(selected_label)

bookings = load(
    "/api/v1/operator/bookings",
    params={"centre_id": centre_id, "slot_date": selected_date.isoformat()} if centre_id else {},
) or []

metric_cols = st.columns(4)
counts = {
    "Total": len(bookings),
    "Waiting": sum(row["token"]["status"] in ("ARRIVED", "WAITING") for row in bookings),
    "Processing": sum(row["token"]["status"] == "PROCESSING" for row in bookings),
    "Completed": sum(row["token"]["status"] == "COMPLETED" for row in bookings),
}
for column, (label, value) in zip(metric_cols, counts.items()):
    column.metric(label, value)

tab_bookings, tab_issues, tab_alerts = st.tabs(["Bookings", "Complaints", "Alerts & notifications"])
with tab_bookings:
    st.subheader("Today's booking desk")
    if bookings:
        rows = [{
            "Booking": row["booking_id"], "Token": row["token"]["token_number"],
            "Farmer": row["farmer_name"], "Crop": row["crop_type"],
            "Slot": f"{row['slot']['start_time']}–{row['slot']['end_time']}",
            "Status": row["token"]["status"], "Payment": row["payment"]["status"],
        } for row in bookings]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        selected_booking = st.selectbox(
            "Open booking detail", [row["booking_id"] for row in bookings],
            format_func=lambda booking_id: next(
                f"{row['token']['token_number']} · {row['farmer_name']}" for row in bookings
                if row["booking_id"] == booking_id
            ),
        )
        detail = load(f"/api/v1/operator/bookings/{selected_booking}")
        if detail:
            st.divider()
            info, workflow = st.columns([1, 1])
            with info:
                st.subheader(f"{detail['farmer_name']} · {detail['booking_id']}")
                st.write(f"**Phone:** {detail['phone']}  \n**Crop:** {detail['crop_type']}  \n"
                         f"**Planned quantity:** {detail['quantity_quintals']} quintals")
                st.write(f"**Token:** {detail['token']['token_number']} · "
                         f"**Queue ahead:** {detail['queue_info']['vehicles_ahead']} · "
                         f"**ETA:** {detail['queue_info']['estimated_wait_min']} min")
            with workflow:
                st.subheader("Operator actions")
                status_now = detail["token"]["status"]
                if status_now in ("BOOKED", "ARRIVED"):
                    label = "Check in" if status_now == "BOOKED" else "Move to waiting"
                    if st.button(label, type="primary"):
                        action("POST", f"/api/v1/operator/bookings/{selected_booking}/check-in")
                with st.form("weighment"):
                    st.markdown("**Weighment**")
                    weight = st.number_input("Weight (kg)", min_value=0.1, value=float(
                        detail["procurement"]["weighment_kg"] or 1.0), step=0.1)
                    accepted = st.selectbox("Quality decision", ["PENDING", "APPROVED", "REJECTED"],
                                            index=["PENDING", "APPROVED", "REJECTED"].index(
                                                detail["procurement"]["accepted_status"]))
                    if st.form_submit_button("Save weighment"):
                        action("POST", f"/api/v1/operator/bookings/{selected_booking}/weighment",
                               json={"weighment_kg": weight, "accepted_status": accepted})
                payment_status = detail["payment"]["status"]
                next_states = {"NOT_STARTED": "PROCUREMENT_COMPLETED",
                               "PROCUREMENT_COMPLETED": "PAYMENT_INITIATED",
                               "PAYMENT_INITIATED": "PROCESSING", "PROCESSING": "PAID"}
                if payment_status in next_states:
                    with st.form("payment"):
                        st.markdown(f"**Payment:** `{payment_status}` → `{next_states[payment_status]}`")
                        amount = st.number_input("Amount (INR)", min_value=0.0,
                                                 value=float(detail["payment"]["amount_inr"] or 0))
                        if st.form_submit_button("Advance payment"):
                            action("PATCH", f"/api/v1/operator/bookings/{selected_booking}/payment",
                                   json={"status": next_states[payment_status], "amount_inr": amount})
    else:
        st.info("No bookings for this centre and date.")

with tab_issues:
    st.subheader("Farmer complaints")
    complaints = load("/api/v1/operator/complaints") or []
    st.dataframe([{
        "ID": row["id"], "Issue": row["issue_type"], "Status": row["status"],
        "Booking": row["booking_id"] or "—", "Created": row["created_at"],
        "Details": row["details"] or "",
    } for row in complaints], use_container_width=True, hide_index=True)

with tab_alerts:
    st.subheader("Escalations")
    if st.button("Scan for 7-day payment stalls"):
        action("POST", "/api/v1/operator/sentinel/payment-escalations")
    escalations = load("/api/v1/operator/escalations") or []
    st.dataframe([{
        "Escalation": row["escalation_id"], "Booking": row["booking_id"],
        "Reason": row["reason"], "Created": row["created_at"],
        "Days stalled": row["payload"].get("days_stalled", "—"),
    } for row in escalations], use_container_width=True, hide_index=True)
    notifications = load("/api/v1/operator/notifications") or []
    st.subheader(f"Notifications ({sum(not row['read'] for row in notifications)} unread)")
    st.dataframe([{
        "Title": row["title"], "Message": row["message"], "Kind": row["kind"],
        "Read": row["read"], "Created": row["created_at"],
    } for row in notifications], use_container_width=True, hide_index=True)
