import api from './api';
import type { Location, LocationCreate, LocationUpdate } from '../types';

export async function listLocations(): Promise<Location[]> {
  const res = await api.get<Location[]>('/api/v1/locations/');
  return res.data;
}

export async function createLocation(data: LocationCreate): Promise<Location> {
  const res = await api.post<Location>('/api/v1/locations/', data);
  return res.data;
}

export async function updateLocation(id: number, data: LocationUpdate): Promise<Location> {
  const res = await api.put<Location>(`/api/v1/locations/${id}`, data);
  return res.data;
}

export async function deleteLocation(id: number): Promise<void> {
  await api.delete(`/api/v1/locations/${id}`);
}

export default { listLocations, createLocation, updateLocation, deleteLocation };
