import api from './api';
import type { SoftwareLicence, LicenceCreate, LicenceUpdate } from '../types';

export async function listLicences(params: { skip?: number; limit?: number; is_active?: boolean; search?: string } = {}): Promise<SoftwareLicence[]> {
  const res = await api.get<SoftwareLicence[]>('/api/v1/licences/', { params });
  return res.data;
}

export async function createLicence(data: LicenceCreate): Promise<SoftwareLicence> {
  const res = await api.post<SoftwareLicence>('/api/v1/licences/', data);
  return res.data;
}

export async function getLicence(id: number): Promise<SoftwareLicence> {
  const res = await api.get<SoftwareLicence>(`/api/v1/licences/${id}`);
  return res.data;
}

export async function updateLicence(id: number, data: LicenceUpdate): Promise<SoftwareLicence> {
  const res = await api.put<SoftwareLicence>(`/api/v1/licences/${id}`, data);
  return res.data;
}

export async function deleteLicence(id: number): Promise<void> {
  await api.delete(`/api/v1/licences/${id}`);
}

export async function assignLicence(licenceId: number, computerId: number): Promise<void> {
  await api.post(`/api/v1/licences/${licenceId}/assign`, { computer_id: computerId });
}

export async function unassignLicence(licenceId: number, computerId: number): Promise<void> {
  await api.delete(`/api/v1/licences/${licenceId}/assign/${computerId}`);
}

export async function getExpiringLicences(days = 30): Promise<SoftwareLicence[]> {
  const res = await api.get<SoftwareLicence[]>('/api/v1/licences/expiring', { params: { days } });
  return res.data;
}

export default {
  listLicences, createLicence, getLicence, updateLicence, deleteLicence,
  assignLicence, unassignLicence, getExpiringLicences,
};
