import api from './api';
import type { SoftwareListResponse, SoftwareSummaryItem, SoftwareQueryParams } from '../types';

export async function getSoftwareInventory(params: SoftwareQueryParams = {}): Promise<SoftwareListResponse> {
  const res = await api.get<SoftwareListResponse>('/api/v1/software/', { params });
  return res.data;
}

export async function getSoftwareSummary(): Promise<SoftwareSummaryItem[]> {
  const res = await api.get<SoftwareSummaryItem[]>('/api/v1/software/summary');
  return res.data;
}

export default { getSoftwareInventory, getSoftwareSummary };
