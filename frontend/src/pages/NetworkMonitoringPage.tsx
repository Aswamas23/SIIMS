import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Wifi } from 'lucide-react';
import networkService from '../services/network.service';
import Table, { Column } from '../components/common/Table';
import Badge from '../components/common/Badge';
import Spinner from '../components/common/Spinner';
import EmptyState from '../components/common/EmptyState';
import { formatRelativeTime } from '../utils/formatters';
import type { NetworkMetric } from '../types';

export default function NetworkMonitoringPage() {
  const [onlyOffline, setOnlyOffline] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['network-status'],
    queryFn: () => networkService.getNetworkStatus({ limit: 200 }),
    refetchInterval: 60_000,
  });

  const rows = (data || []).filter((m) => (onlyOffline ? m.is_up === false : true));

  const columns: Column<NetworkMetric>[] = [
    { key: 'computer_id', header: 'Computer', render: (m) => `PC #${m.computer_id}` },
    {
      key: 'is_up',
      header: 'Status',
      render: (m) => (m.is_up ? <Badge variant="green">Up</Badge> : <Badge variant="red">Down</Badge>),
    },
    { key: 'ip_address', header: 'IP Address', render: (m) => m.ip_address || '—' },
    { key: 'interface_name', header: 'Interface', render: (m) => m.interface_name || '—' },
    { key: 'latency_ms', header: 'Latency', render: (m) => m.latency_ms !== null ? `${m.latency_ms.toFixed(0)} ms` : '—' },
    { key: 'packet_loss_percent', header: 'Packet Loss', render: (m) => m.packet_loss_percent !== null ? `${m.packet_loss_percent.toFixed(1)}%` : '—' },
    { key: 'server_reachable', header: 'Server', render: (m) => (m.server_reachable ? '✅' : m.server_reachable === false ? '❌' : '—') },
    { key: 'recorded_at', header: 'Last Check', render: (m) => formatRelativeTime(m.recorded_at) },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Network Monitoring</h1>
        <div className="flex items-center gap-3">
          <label className="text-sm text-slate-600 flex items-center gap-2">
            <input type="checkbox" checked={onlyOffline} onChange={(e) => setOnlyOffline(e.target.checked)} className="rounded" />
            Show only offline
          </label>
          <span className="text-xs text-slate-500 flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" /> Auto-refresh: 60s
          </span>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-10"><Spinner /></div>
        ) : rows.length === 0 ? (
          <EmptyState icon={<Wifi className="h-10 w-10" />} title="No network metrics" description="Monitoring agents will report network status here." />
        ) : (
          <Table
            columns={columns}
            data={rows}
            rowKey={(m) => m.id}
          />
        )}
      </div>
    </div>
  );
}
