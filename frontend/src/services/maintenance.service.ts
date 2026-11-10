import api from './api';
import type { MaintenanceRecord, MaintenanceCreate, MaintenanceCompleteRequest } from '../types';

export async function listMaintenance(params: { skip?: number; limit?: number } = {}): Promise<MaintenanceRecord[]> {
  const res = await api.get<MaintenanceRecord[]>('/api/v1/maintenance/', { params });
  return res.data;
}

export async function createMaintenance(data: MaintenanceCreate): Promise<MaintenanceRecord> {
  const res = await api.post<MaintenanceRecord>('/api/v1/maintenance/', data);
  return res.data;
}

export async function getMaintenance(id: number): Promise<MaintenanceRecord> {
  const res = await api.get<MaintenanceRecord>(`/api/v1/maintenance/${id}`);
  return res.data;
}

export async function completeMaintenance(id: number, data: MaintenanceCompleteRequest): Promise<MaintenanceRecord> {
  const res = await api.post<MaintenanceRecord>(`/api/v1/maintenance/${id}/complete`, data);
  return res.data;
}

export default { listMaintenance, createMaintenance, getMaintenance, completeMaintenance };
