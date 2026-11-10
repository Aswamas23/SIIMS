import api from './api';
import type { Notification, NotificationListResponse } from '../types';

export async function getNotifications(params: { skip?: number; limit?: number } = {}): Promise<NotificationListResponse> {
  const res = await api.get<NotificationListResponse>('/api/v1/notifications/', { params });
  return res.data;
}

export async function markRead(id: number): Promise<Notification> {
  const res = await api.put<Notification>(`/api/v1/notifications/${id}/read`);
  return res.data;
}

export async function markAllRead(): Promise<void> {
  await api.put('/api/v1/notifications/read-all');
}

export async function deleteNotification(id: number): Promise<void> {
  await api.delete(`/api/v1/notifications/${id}`);
}

export default { getNotifications, markRead, markAllRead, deleteNotification };
