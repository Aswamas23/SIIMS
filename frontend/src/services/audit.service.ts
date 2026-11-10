import api from './api';
import type { AuditLogListResponse, AuditQueryParams } from '../types';

export async function getAuditLogs(params: AuditQueryParams = {}): Promise<AuditLogListResponse> {
  const res = await api.get<AuditLogListResponse>('/api/v1/audit/', { params });
  return res.data;
}

export default { getAuditLogs };
