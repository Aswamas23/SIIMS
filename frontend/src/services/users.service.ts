import api from './api';
import type { User, UserCreate, UserUpdate, UserListResponse, ResetPasswordResponse } from '../types';

export async function getUsers(params: { skip?: number; limit?: number } = {}): Promise<UserListResponse> {
  const res = await api.get<UserListResponse>('/api/v1/users/', { params });
  return res.data;
}

export async function createUser(data: UserCreate): Promise<User> {
  const res = await api.post<User>('/api/v1/users/', data);
  return res.data;
}

export async function getUser(id: number): Promise<User> {
  const res = await api.get<User>(`/api/v1/users/${id}`);
  return res.data;
}

export async function updateUser(id: number, data: UserUpdate): Promise<User> {
  const res = await api.put<User>(`/api/v1/users/${id}`, data);
  return res.data;
}

export async function deactivateUser(id: number): Promise<void> {
  await api.delete(`/api/v1/users/${id}`);
}

export async function resetPassword(id: number): Promise<ResetPasswordResponse> {
  const res = await api.post<ResetPasswordResponse>(`/api/v1/users/${id}/reset-password`);
  return res.data;
}

export default { getUsers, createUser, getUser, updateUser, deactivateUser, resetPassword };
