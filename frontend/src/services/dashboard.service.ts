import api from './api';
import type { DashboardStats, Computer, ComputerListResponse, Alert, Incident, SoftwareLicence } from '../types';

/**
 * The backend has no dedicated /dashboard/stats endpoint, so this service
 * aggregates the dashboard summary by calling several endpoints in parallel.
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  const [computersRes, alertsRes, incidentsRes, expiringRes] = await Promise.all([
    api.get<ComputerListResponse>('/api/v1/computers/', { params: { limit: 500 } }),
    api.get<Alert[]>('/api/v1/hardware/alerts'),
    api.get<Incident[]>('/api/v1/incidents/', { params: { limit: 500 } }),
    api.get<SoftwareLicence[]>('/api/v1/licences/expiring', { params: { days: 30 } }),
  ]);

  const computers: Computer[] = computersRes.data.items;
  const total = computersRes.data.total;

  const counts: Record<string, number> = {
    online: 0, offline: 0, warning: 0, critical: 0, maintenance: 0, unknown: 0,
  };
  for (const c of computers) {
    counts[c.status] = (counts[c.status] || 0) + 1;
  }

  const openIncidents = incidentsRes.data.filter(
    (i) => i.status === 'open' || i.status === 'in_progress',
  ).length;

  return {
    total_computers: total,
    online_computers: counts.online || 0,
    offline_computers: counts.offline || 0,
    warning_computers: counts.warning || 0,
    critical_computers: counts.critical || 0,
    unknown_computers: counts.unknown || 0,
    active_alerts: alertsRes.data.length,
    open_incidents: openIncidents,
    expiring_licences: expiringRes.data.length,
    status_distribution: [
      { name: 'Online', value: counts.online || 0 },
      { name: 'Offline', value: counts.offline || 0 },
      { name: 'Warning', value: counts.warning || 0 },
      { name: 'Critical', value: counts.critical || 0 },
      { name: 'Unknown', value: counts.unknown || 0 },
    ],
  };
}

export async function getRecentAlerts(): Promise<Alert[]> {
  const res = await api.get<Alert[]>('/api/v1/hardware/alerts');
  return res.data.slice(0, 10);
}

export async function getRecentIncidents(): Promise<Incident[]> {
  const res = await api.get<Incident[]>('/api/v1/incidents/', { params: { limit: 10 } });
  return res.data;
}

export default { getDashboardStats, getRecentAlerts, getRecentIncidents };
