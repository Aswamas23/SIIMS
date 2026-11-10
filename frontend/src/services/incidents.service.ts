import api from './api';
import type { Incident, IncidentCreate, IncidentUpdateSchema, IncidentQueryParams, UpdateType } from '../types';

export async function listIncidents(params: IncidentQueryParams = {}): Promise<Incident[]> {
  const res = await api.get<Incident[]>('/api/v1/incidents/', { params });
  return res.data;
}

export async function createIncident(data: IncidentCreate): Promise<Incident> {
  const res = await api.post<Incident>('/api/v1/incidents/', data);
  return res.data;
}

export async function getIncident(id: number): Promise<Incident> {
  const res = await api.get<Incident>(`/api/v1/incidents/${id}`);
  return res.data;
}

export async function updateIncident(id: number, data: IncidentUpdateSchema): Promise<Incident> {
  const res = await api.put<Incident>(`/api/v1/incidents/${id}`, data);
  return res.data;
}

export async function assignIncident(id: number, userId: number): Promise<void> {
  await api.post(`/api/v1/incidents/${id}/assign`, { user_id: userId });
}

export async function addIncidentUpdate(id: number, message: string, updateType: UpdateType = 'comment'): Promise<void> {
  await api.post(`/api/v1/incidents/${id}/update`, { message, update_type: updateType });
}

export async function resolveIncident(id: number, resolutionNotes?: string): Promise<void> {
  await api.post(`/api/v1/incidents/${id}/resolve`, { resolution_notes: resolutionNotes });
}

export async function closeIncident(id: number): Promise<void> {
  await api.post(`/api/v1/incidents/${id}/close`);
}

export default {
  listIncidents, createIncident, getIncident, updateIncident, assignIncident,
  addIncidentUpdate, resolveIncident, closeIncident,
};
