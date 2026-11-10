import api from './api';
import type {
  Computer, ComputerCreate, ComputerUpdate, ComputerListResponse, ComputerQueryParams,
  HardwareMetric, NetworkMetric, InstalledSoftware, Incident, MaintenanceRecord, Alert,
  AgentKeyResponse,
} from '../types';

export async function listComputers(params: ComputerQueryParams = {}): Promise<ComputerListResponse> {
  const res = await api.get<ComputerListResponse>('/api/v1/computers/', { params });
  return res.data;
}

export async function createComputer(data: ComputerCreate): Promise<Computer> {
  const res = await api.post<Computer>('/api/v1/computers/', data);
  return res.data;
}

export async function getComputer(id: number): Promise<Computer> {
  const res = await api.get<Computer>(`/api/v1/computers/${id}`);
  return res.data;
}

export async function updateComputer(id: number, data: ComputerUpdate): Promise<Computer> {
  const res = await api.put<Computer>(`/api/v1/computers/${id}`, data);
  return res.data;
}

export async function deactivateComputer(id: number): Promise<void> {
  await api.delete(`/api/v1/computers/${id}`);
}

export async function getComputerHardwareMetrics(id: number, limit = 100): Promise<HardwareMetric[]> {
  const res = await api.get<HardwareMetric[]>(`/api/v1/computers/${id}/hardware-metrics`, {
    params: { limit },
  });
  return res.data;
}

export async function getComputerNetworkMetrics(id: number, limit = 100): Promise<NetworkMetric[]> {
  const res = await api.get<NetworkMetric[]>(`/api/v1/computers/${id}/network-metrics`, {
    params: { limit },
  });
  return res.data;
}

export async function getComputerSoftware(id: number): Promise<InstalledSoftware[]> {
  const res = await api.get<InstalledSoftware[]>(`/api/v1/computers/${id}/software`);
  return res.data;
}

export async function getComputerIncidents(id: number): Promise<Incident[]> {
  const res = await api.get<Incident[]>(`/api/v1/computers/${id}/incidents`);
  return res.data;
}

export async function getComputerMaintenance(id: number): Promise<MaintenanceRecord[]> {
  const res = await api.get<MaintenanceRecord[]>(`/api/v1/computers/${id}/maintenance`);
  return res.data;
}

export async function getComputerAlerts(id: number): Promise<Alert[]> {
  const res = await api.get<Alert[]>(`/api/v1/computers/${id}/alerts`);
  return res.data;
}

export async function generateAgentKey(id: number): Promise<AgentKeyResponse> {
  const res = await api.post<AgentKeyResponse>(`/api/v1/computers/${id}/generate-agent-key`);
  return res.data;
}

export default {
  listComputers, createComputer, getComputer, updateComputer, deactivateComputer,
  getComputerHardwareMetrics, getComputerNetworkMetrics, getComputerSoftware,
  getComputerIncidents, getComputerMaintenance, getComputerAlerts, generateAgentKey,
};
