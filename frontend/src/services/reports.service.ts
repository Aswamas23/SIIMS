import api from './api';
import type { ReportType, ReportFormat, ReportFilters } from '../types';

/**
 * Downloads a report file from the backend. The endpoint returns a binary blob
 * with a Content-Disposition attachment header; we trigger a browser download
 * via a temporary anchor element.
 */
export async function downloadReport(
  type: ReportType,
  format: ReportFormat,
  filters: ReportFilters = {},
): Promise<void> {
  const res = await api.get(`/api/v1/reports/${type}`, {
    params: { format, ...filters },
    responseType: 'blob',
  });

  // Derive filename from the Content-Disposition header if present, else fallback.
  const disposition = res.headers['content-disposition'] as string | undefined;
  let filename = `siims_${type}_report.${format === 'excel' ? 'xlsx' : format}`;
  if (disposition) {
    const match = disposition.match(/filename=([^;]+)/);
    if (match) filename = match[1].replace(/"/g, '');
  }

  const url = window.URL.createObjectURL(res.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

export default { downloadReport };
