import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ClipboardList } from 'lucide-react';
import auditService from '../services/audit.service';
import Table, { Column } from '../components/common/Table';
import Pagination from '../components/common/Pagination';
import DateRangePicker from '../components/common/DateRangePicker';
import EmptyState from '../components/common/EmptyState';
import { useAuth } from '../hooks/useAuth';
import { formatDateTime } from '../utils/formatters';
import type { AuditLog, AuditQueryParams } from '../types';

const PAGE_SIZE = 25;

export default function AuditLogsPage() {
  const { user } = useAuth();
  const [page, setPage] = useState(1);
  const [userId, setUserId] = useState('');
  const [entityType, setEntityType] = useState('');
  const [action, setAction] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');

  if (user?.role !== 'system_admin') {
    return <div className="py-20 text-center text-slate-500">You do not have permission to view this page.</div>;
  }

  const params: AuditQueryParams = {
    skip: (page - 1) * PAGE_SIZE,
    limit: PAGE_SIZE,
    user_id: userId ? Number(userId) : undefined,
    entity_type: entityType || undefined,
    action: action || undefined,
    date_from: from || undefined,
    date_to: to || undefined,
  };

  const { data, isLoading } = useQuery({
    queryKey: ['audit', params],
    queryFn: () => auditService.getAuditLogs(params),
  });

  const columns: Column<AuditLog>[] = [
    { key: 'created_at', header: 'Timestamp', render: (l) => formatDateTime(l.created_at) },
    { key: 'user_id', header: 'User ID', render: (l) => l.user_id ?? '—' },
    { key: 'action', header: 'Action', render: (l) => <span className="font-mono text-xs">{l.action}</span> },
    { key: 'entity_type', header: 'Entity', render: (l) => l.entity_type || '—' },
    { key: 'entity_id', header: 'Entity ID', render: (l) => l.entity_id ?? '—' },
    { key: 'ip_address', header: 'IP', render: (l) => l.ip_address || '—' },
    {
      key: 'details',
      header: 'Details',
      render: (l) => {
        if (!l.details) return '—';
        const s = JSON.stringify(l.details);
        return <span className="text-xs text-slate-500 truncate block max-w-xs" title={s}>{s}</span>;
      },
    },
  ];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">Audit Logs</h1>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">User ID</label>
          <input type="number" value={userId} onChange={(e) => setUserId(e.target.value)} placeholder="—"
            className="w-24 px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Entity Type</label>
          <input value={entityType} onChange={(e) => setEntityType(e.target.value)} placeholder="computer, user…"
            className="w-32 px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">Action</label>
          <input value={action} onChange={(e) => setAction(e.target.value)} placeholder="create_…"
            className="w-32 px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <DateRangePicker from={from} to={to} onFromChange={setFrom} onToChange={setTo} />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="py-10 text-center text-slate-500">Loading…</div>
        ) : (data?.items.length ?? 0) === 0 ? (
          <EmptyState icon={<ClipboardList className="h-10 w-10" />} title="No audit log entries" />
        ) : (
          <>
            <Table columns={columns} data={data?.items || []} rowKey={(l) => l.id} />
            <div className="px-4">
              <Pagination page={page} pages={data?.pages || 1} total={data?.total || 0} onPageChange={setPage} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
