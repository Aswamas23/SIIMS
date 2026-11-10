import { useQuery } from '@tanstack/react-query';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, AreaChart, Area, Legend,
} from 'recharts';
import {
  Monitor, CheckCircle, XCircle, AlertTriangle, Flame, Key, Clock,
} from 'lucide-react';
import StatCard from '../components/common/StatCard';
import Spinner from '../components/common/Spinner';
import Table, { Column } from '../components/common/Table';
import SeverityBadge from '../components/common/SeverityBadge';
import StatusBadge from '../components/common/StatusBadge';
import EmptyState from '../components/common/EmptyState';
import dashboardService from '../services/dashboard.service';
import hardwareService from '../services/hardware.service';
import { formatRelativeTime, titleCase } from '../utils/formatters';
import type { Alert, Incident } from '../types';

const STATUS_COLORS: Record<string, string> = {
  Online: '#16a34a', Offline: '#dc2626', Warning: '#eab308',
  Critical: '#ea580c', Unknown: '#94a3b8',
};

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardService.getDashboardStats,
    refetchInterval: 30_000,
  });

  const { data: alerts } = useQuery({
    queryKey: ['dashboard-alerts'],
    queryFn: dashboardService.getRecentAlerts,
    refetchInterval: 30_000,
  });

  const { data: incidents } = useQuery({
    queryKey: ['dashboard-incidents'],
    queryFn: dashboardService.getRecentIncidents,
    refetchInterval: 30_000,
  });

  const { data: metrics } = useQuery({
    queryKey: ['dashboard-hardware-metrics'],
    queryFn: () => hardwareService.getHardwareMetrics({ limit: 200 }),
    refetchInterval: 30_000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  // Top 10 by CPU for the bar charts.
  const byCpu = [...(metrics || [])]
    .filter((m) => m.cpu_percent !== null)
    .sort((a, b) => (b.cpu_percent ?? 0) - (a.cpu_percent ?? 0))
    .slice(0, 10)
    .map((m) => ({ name: `PC #${m.computer_id}`, cpu: Number((m.cpu_percent ?? 0).toFixed(1)) }));

  const byRam = [...(metrics || [])]
    .filter((m) => m.ram_percent !== null)
    .sort((a, b) => (b.ram_percent ?? 0) - (a.ram_percent ?? 0))
    .slice(0, 10)
    .map((m) => ({ name: `PC #${m.computer_id}`, ram: Number((m.ram_percent ?? 0).toFixed(1)) }));

  const byDisk = [...(metrics || [])]
    .filter((m) => m.disk_percent !== null)
    .map((m) => ({ name: `PC #${m.computer_id}`, disk: Number((m.disk_percent ?? 0).toFixed(1)) }))
    .slice(0, 20);

  const alertColumns: Column<Alert>[] = [
    { key: 'computer_id', header: 'Computer', render: (a) => `PC #${a.computer_id}` },
    { key: 'alert_type', header: 'Type', render: (a) => titleCase(a.alert_type) },
    { key: 'severity', header: 'Severity', render: (a) => <SeverityBadge severity={a.severity} /> },
    { key: 'title', header: 'Title', render: (a) => a.title },
    { key: 'created_at', header: 'Time', render: (a) => formatRelativeTime(a.created_at) },
  ];

  const incidentColumns: Column<Incident>[] = [
    { key: 'incident_number', header: 'Number', render: (i) => i.incident_number },
    { key: 'title', header: 'Title' },
    { key: 'severity', header: 'Severity', render: (i) => <SeverityBadge severity={i.severity} /> },
    { key: 'status', header: 'Status', render: (i) => titleCase(i.status) },
    { key: 'created_at', header: 'Reported', render: (i) => formatRelativeTime(i.created_at) },
  ];

  return (
    <div className="space-y-6">
      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Computers" value={stats?.total_computers ?? 0} icon={<Monitor className="h-6 w-6 text-white" />} color="blue" />
        <StatCard title="Online" value={stats?.online_computers ?? 0} icon={<CheckCircle className="h-6 w-6 text-white" />} color="green" />
        <StatCard title="Offline" value={stats?.offline_computers ?? 0} icon={<XCircle className="h-6 w-6 text-white" />} color="red" />
        <StatCard title="Warnings" value={stats?.warning_computers ?? 0} icon={<AlertTriangle className="h-6 w-6 text-white" />} color="yellow" />
        <StatCard title="Critical Incidents" value={stats?.open_incidents ?? 0} icon={<Flame className="h-6 w-6 text-white" />} color="orange" />
        <StatCard title="Active Alerts" value={stats?.active_alerts ?? 0} icon={<AlertTriangle className="h-6 w-6 text-white" />} color="red" />
        <StatCard title="Expiring Licences" value={stats?.expiring_licences ?? 0} icon={<Clock className="h-6 w-6 text-white" />} color="purple" />
        <StatCard title="Unknown Status" value={stats?.unknown_computers ?? 0} icon={<Key className="h-6 w-6 text-white" />} color="blue" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="font-semibold text-slate-800 mb-4">Computer Status</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={stats?.status_distribution || []}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={90}
                label={(e) => `${e.name}: ${e.value}`}
              >
                {(stats?.status_distribution || []).map((entry) => (
                  <Cell key={entry.name} fill={STATUS_COLORS[entry.name] || '#94a3b8'} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="font-semibold text-slate-800 mb-4">Top 10 — CPU Usage</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={byCpu} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} unit="%" />
              <YAxis type="category" dataKey="name" width={70} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="cpu" fill="#2563eb" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="font-semibold text-slate-800 mb-4">Top 10 — RAM Usage</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={byRam} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} unit="%" />
              <YAxis type="category" dataKey="name" width={70} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="ram" fill="#7c3aed" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="font-semibold text-slate-800 mb-4">Disk Usage by Computer</h3>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={byDisk}>
              <defs>
                <linearGradient id="diskGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.5} />
                  <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" height={60} />
              <YAxis domain={[0, 100]} unit="%" />
              <Tooltip />
              <Area type="monotone" dataKey="disk" stroke="#0ea5e9" fill="url(#diskGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent alerts + incidents */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="font-semibold text-slate-800 mb-4">Recent Alerts</h3>
          {(alerts || []).length === 0 ? (
            <EmptyState title="No active alerts" description="All systems nominal." />
          ) : (
            <Table columns={alertColumns} data={alerts || []} rowKey={(a) => a.id} />
          )}
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="font-semibold text-slate-800 mb-4">Recent Incidents</h3>
          {(incidents || []).length === 0 ? (
            <EmptyState title="No recent incidents" />
          ) : (
            <Table columns={incidentColumns} data={incidents || []} rowKey={(i) => i.id} />
          )}
        </div>
      </div>

      {/* Status breakdown quick view */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <h3 className="font-semibold text-slate-800 mb-4">Status Breakdown</h3>
        <div className="flex flex-wrap gap-3">
          {(['online', 'offline', 'warning', 'critical', 'unknown'] as const).map((s) => (
            <div key={s} className="flex items-center gap-2">
              <StatusBadge status={s} />
              <span className="text-slate-700 font-medium">
                {stats ? (stats as unknown as Record<string, number>)[`${s}_computers`] ?? 0 : 0}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
