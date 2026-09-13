import { Platform } from 'react-native';

export type FarmerProfile = { id: string; name: string; phone: string; aadhaar_hash: string | null; land_hectares: number | null; created_at: string };
export type AuthResponse = { access_token: string; token_type: 'bearer'; farmer: FarmerProfile };
export type Slot = { date: string; start_time: string; end_time: string; capacity: number; booked: number; available: number };
export type Booking = { booking_id: string; farmer_id: string; farmer_name: string; phone: string; centre_id: string; centre_name: string; crop_type: string; quantity_quintals: number; slot: { date: string; start_time: string; end_time: string }; token: { token_number: string; issued_at: string; status: string }; queue_info: { vehicles_ahead: number; estimated_wait_min: number; last_updated: string }; procurement: Record<string, unknown>; payment: Record<string, unknown> };
export type Payment = { payment_id: string; booking_id: string; status: string; amount_inr: number | null; initiated_at: string | null; paid_at: string | null; days_stalled: number };
export type Complaint = { id: string; farmer_id: string; booking_id: string | null; issue_type: string; details: string | null; status: string; created_at: string; updated_at: string };
export type Notification = { id: string; farmer_id: string; title: string; message: string; kind: string; read: boolean; created_at: string };
export type Receipt = { receipt_id: string; booking_id: string; farmer_id: string; centre_id: string; crop_type: string; weighment_kg: number; accepted_status: string; completed_at: string; issued_at: string };
export const API_URL = process.env.EXPO_PUBLIC_API_URL || (Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000');

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...(options.headers || {}) } });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body as T;
}
const auth = (token: string) => ({ Authorization: "Bearer " + token });
export const api = {
  requestOtp: (phone: string) => request<{ phone: string; expires_in_seconds: number; development_otp: string; message: string }>('/api/v1/auth/request-otp', { method: 'POST', body: JSON.stringify({ phone }) }),
  verifyOtp: (phone: string, otp: string) => request<AuthResponse>('/api/v1/auth/verify-otp', { method: 'POST', body: JSON.stringify({ phone, otp }) }),
  profile: (token: string) => request<FarmerProfile>('/api/v1/farmer/profile', { headers: auth(token) }),
  availability: (centreId: string, date: string) => request<{ centre_id: string; date: string; slots: Slot[] }>(`/api/v1/slots/availability?centre_id=${encodeURIComponent(centreId)}&slot_date=${date}`),
  createBooking: (token: string, body: { centre_id: string; crop_type: string; quantity_quintals: number; slot_date: string; slot_start_time: string; slot_end_time: string }) => request<Booking>('/api/v1/bookings/create', { method: 'POST', headers: auth(token), body: JSON.stringify(body) }),
  bookings: (token: string) => request<Booking[]>('/api/v1/bookings', { headers: auth(token) }),
  booking: (token: string, id: string) => request<Booking>(`/api/v1/bookings/${id}`, { headers: auth(token) }),
  cancelBooking: (token: string, id: string) => request<Booking>(`/api/v1/bookings/${id}/cancel`, { method: 'POST', headers: auth(token) }),
  queueStatus: (token: string, id: string) => request<{ booking_id: string; token_number: string; token_status: string; vehicles_ahead: number; estimated_wait_min: number; last_updated: string }>(`/api/v1/queue/status/${id}`, { headers: auth(token) }),
  payments: (token: string) => request<Payment[]>('/api/v1/farmer/payments', { headers: auth(token) }),
  payment: (token: string, id: string) => request<Payment>(`/api/v1/farmer/payments/${id}`, { headers: auth(token) }),
  receipt: (token: string, id: string) => request<Receipt>(`/api/v1/farmer/bookings/${id}/receipt`, { headers: auth(token) }),
  complaints: (token: string) => request<Complaint[]>('/api/v1/farmer/complaints', { headers: auth(token) }),
  createComplaint: (token: string, body: { issue_type: string; details?: string; booking_id?: string }) => request<Complaint>('/api/v1/farmer/complaints', { method: 'POST', headers: auth(token), body: JSON.stringify(body) }),
  notifications: (token: string) => request<Notification[]>('/api/v1/farmer/notifications', { headers: auth(token) }),
  markNotificationRead: (token: string, id: string) => request<Notification>(`/api/v1/farmer/notifications/${id}/read`, { method: 'PATCH', headers: auth(token) }),
};
