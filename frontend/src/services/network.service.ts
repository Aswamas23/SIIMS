import api from './api';
import type { NetworkMetric } from '../types';

export async function getNetworkStatus(params: { skip?: number; limit?: number } = {}): Promise<NetworkMetric[]> {
  const res = await api.get<NetworkMetric[]>('/api/v1/network/status', { params });
  return res.data;
}

export async function getNetworkMetrics(computerId: number, limit = 100): Promise<NetworkMetric[]> {
  const res = await api.get<NetworkMetric[]>('/api/v1/network/metrics', {
    params: { computer_id: computerId, limit },
  });
  return res.data;
}

export default { getNetworkStatus, getNetworkMetrics };
