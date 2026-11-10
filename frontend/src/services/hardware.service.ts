import api from './api';
import type { HardwareMetric, Alert, Threshold, ThresholdUpdate } from '../types';

export async function getHardwareMetrics(params: { skip?: number; limit?: number } = {}): Promise<HardwareMetric[]> {
  const res = await api.get<HardwareMetric[]>('/api/v1/hardware/metrics', { params });
  return res.data;
}

export async function getHardwareAlerts(): Promise<Alert[]> {
  const res = await api.get<Alert[]>('/api/v1/hardware/alerts');
  return res.data;
}

export async function getThresholds(): Promise<Threshold> {
  const res = await api.get<Threshold>('/api/v1/hardware/thresholds');
  return res.data;
}

export async function updateThresholds(data: ThresholdUpdate): Promise<Threshold> {
  const res = await api.put<Threshold>('/api/v1/hardware/thresholds', data);
  return res.data;
}

export default { getHardwareMetrics, getHardwareAlerts, getThresholds, updateThresholds };
