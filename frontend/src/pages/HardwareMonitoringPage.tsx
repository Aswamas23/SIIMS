import { useHardwareMetrics } from '../hooks/useHardware';
import Table, { Column } from '../components/common/Table';
import ProgressBar from '../components/common/ProgressBar';
import Spinner from '../components/common/Spinner';
import EmptyState from '../components/common/EmptyState';
import { Cpu } from 'lucide-react';
import { formatRelativeTime, formatUptime, titleCase } from '../utils/formatters';
import type { HardwareMetric } from '../types';

export default function HardwareMonitoringPage() {
  const { data, isLoading } = useHardwareMetrics({ limit: 200 });

  const columns: Column<HardwareMetric>[] = [
    { key: 'computer_id', header: 'Computer', render: (m) => `PC #${m.computer_id}` },
    {
      key: 'cpu_percent',
      header: 'CPU',
      render: (m) => <ProgressBar value={m.cpu_percent} warningThreshold={90} criticalThreshold={95} />,
    },
    {
      key: 'ram_percent',
      header: 'RAM',
      render: (m) => <ProgressBar value={m.ram_percent} warningThreshold={90} criticalThreshold={95} />,
    },
    {
      key: 'disk_percent',
      header: 'Disk',
      render: (m) => <ProgressBar value={m.disk_percent} warningThreshold={90} criticalThreshold={95} />,
    },
    { key: 'cpu_temp_celsius', header: 'Temp', render: (m) => m.cpu_temp_celsius !== null ? `${m.cpu_temp_celsius.toFixed(0)}°C` : 'N/A' },
    { key: 'uptime_seconds', header: 'Uptime', render: (m) => formatUptime(m.uptime_seconds) },
    { key: 'recorded_at', header: 'Updated', render: (m) => formatRelativeTime(m.recorded_at) },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Hardware Monitoring</h1>
        <span className="text-xs text-slate-500 flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" /> Auto-refresh: 30s
        </span>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-10"><Spinner /></div>
        ) : (data?.length ?? 0) === 0 ? (
          <EmptyState icon={<Cpu className="h-10 w-10" />} title="No hardware metrics yet" description="Start a monitoring agent on a computer to populate this view." />
        ) : (
          <Table columns={columns} data={data || []} rowKey={(m) => m.id} />
        )}
      </div>

      {/* Legend */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <h3 className="font-semibold text-slate-800 mb-2">Threshold Legend</h3>
        <div className="flex flex-wrap gap-4 text-sm text-slate-600">
          <div className="flex items-center gap-2"><span className="h-3 w-6 bg-green-500 rounded" /> Normal (&lt;90%)</div>
          <div className="flex items-center gap-2"><span className="h-3 w-6 bg-yellow-500 rounded" /> Warning (90–95%)</div>
          <div className="flex items-center gap-2"><span className="h-3 w-6 bg-red-500 rounded" /> Critical (≥95%)</div>
        </div>
        <p className="text-xs text-slate-400 mt-2">{titleCase('Configure thresholds in Settings → Thresholds.')}</p>
      </div>
    </div>
  );
}
