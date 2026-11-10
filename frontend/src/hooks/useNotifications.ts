import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import notificationsService from '../services/notifications.service';

export function useNotifications(params: { skip?: number; limit?: number } = {}) {
  const query = useQuery({
    queryKey: ['notifications', params],
    queryFn: () => notificationsService.getNotifications(params),
    refetchInterval: 60_000,
  });
  const unreadCount = query.data?.unread_count ?? 0;
  return { ...query, unreadCount };
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => notificationsService.markRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
}

export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => notificationsService.markAllRead(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
}

export function useDeleteNotification() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => notificationsService.deleteNotification(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
}
