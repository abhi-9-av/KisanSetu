import { Platform } from 'react-native';

export type FarmerProfile = {
  id: string;
  name: string;
  phone: string;
  aadhaar_hash: string | null;
  land_hectares: number | null;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: 'bearer';
  farmer: FarmerProfile;
};

// Override with EXPO_PUBLIC_API_URL (for example http://192.168.1.20:8000).
export const API_URL =
  process.env.EXPO_PUBLIC_API_URL ||
  (Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000');

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body as T;
}

export const api = {
  requestOtp: (phone: string) =>
    request<{ phone: string; expires_in_seconds: number; development_otp: string; message: string }>(
      '/api/v1/auth/request-otp',
      { method: 'POST', body: JSON.stringify({ phone }) },
    ),
  verifyOtp: (phone: string, otp: string) =>
    request<AuthResponse>('/api/v1/auth/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ phone, otp }),
    }),
  profile: (token: string) =>
    request<FarmerProfile>('/api/v1/farmer/profile', {
      headers: { Authorization: `Bearer ${token}` },
    }),
};
