import api, { setAccessToken } from './api';
import type { TokenResponse, ChangePasswordRequest, User, UserUpdate } from '../types';

export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await api.post<TokenResponse>('/api/v1/auth/login', { email, password });
  const tokens = res.data;
  localStorage.setItem('refresh_token', tokens.refresh_token);
  setAccessToken(tokens.access_token);
  return tokens;
}

export async function logout(): Promise<void> {
  const refreshToken = localStorage.getItem('refresh_token');
  try {
    await api.post('/api/v1/auth/logout', { refresh_token: refreshToken });
  } catch {
    // Ignore errors on logout — we clear the token locally regardless.
  } finally {
    localStorage.removeItem('refresh_token');
    setAccessToken(null);
  }
}

export async function getMe(): Promise<User> {
  const res = await api.get<User>('/api/v1/auth/me');
  return res.data;
}

export async function updateMe(data: UserUpdate): Promise<User> {
  const res = await api.put<User>('/api/v1/auth/me', data);
  return res.data;
}

export async function changePassword(data: ChangePasswordRequest): Promise<void> {
  await api.post('/api/v1/auth/me/change-password', data);
}

export default { login, logout, getMe, updateMe, changePassword };
