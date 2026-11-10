import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Cpu, MemoryStick, HardDrive, Clock, Key } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { useComputer } from '../hooks/useComputers';
import computersService from '../services/computers.service';
import locationsService from '../services/locations.service';
import StatusBadge from '../components/common/StatusBadge';
import Button from '../components/common/Button';
import Spinner from '../components/common/Spinner';
import Table, { Column } from '../components/common/Table';
import SeverityBadge from '../components/common/SeverityBadge';
import { useAuth } from '../hooks/useAuth';
import { formatDate, formatDateTime, formatRelativeTime, formatUptime, titleCase } from '../utils/formatters';
import type {
  InstalledSoftware, NetworkMetric, Incident,
  MaintenanceRecord,
} from '../types';

type Tab = 'overview' | 'hardware' | 'software' | 'network' | 'incidents' | 'maintenance';

export default function ComputerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const computerId = Number(id);
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.role === 'system_admin';
  const [tab, setTab] = useState<Tab>('overview');
  const [agentKey, setAgentKey] = useState<string | null>(null);

  const { data: computer, isLoading } = useComputer(computerId);
  const { data: locations } = useQuery({ queryKey: ['locations'], queryFn: locationsService.listLocations });

  const { data: hwMetrics } = useQuery({
    queryKey: ['computer-hw', computerId],
    queryFn: () => computersService.getComputerHardwareMetrics(computerId, 50),
    enabled: !!computerId,
  });
  const { data: sw } = useQuery({
    queryKey: ['computer-sw', computerId],
    queryFn: () => computersService.getComputerSoftware(computerId),
    enabled: !!computerId,
  });
  const { data: netMetrics } = useQuery({
    queryKey: ['computer-net', computerId],
    queryFn: () => computersService.getComputerNetworkMetrics(computerId, 50),
    enabled: !!computerId,
  });
  const { data: incidents } = useQuery({
    queryKey: ['computer-inc', computerId],
    queryFn: () => computersService.getComputerIncidents(computerId),
    enabled: !!computerId,
  });
  const { data: maintenance } = useQuery({
    queryKey: ['computer-main', computerId],
    queryFn: () => computersService.getComputerMaintenance(computerId),
    enabled: !!computerId,
  });

  if (isLoading) {
    return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;
  }

  if (!computer) {
    return <div className="py-20 text-center text-slate-500">Computer not found.</div>;
  }

  const locationName = locations?.find((l) => l.id === computer.location_id)?.name || '—';
  const latestHw = hwMetrics && hwMetrics.length > 0 ? hwMetrics[0] : null;

  // Chart data (reverse so oldest → newest left to right).
  const hwChart = [...(hwMetrics || [])].reverse().map((m) => ({
    time: new Date(m.recorded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    cpu: m.cpu_percent, ram: m.ram_percent, disk: m.disk_percent,
  }));

  const generateKey = async () => {
    try {
      const res = await computersService.generateAgentKey(computerId);
      setAgentKey(res.api_key);
    } catch {
      setAgentKey('Failed to generate key.');
    }
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'hardware', label: 'Hardware' },
    { key: 'software', label: 'Software' },
    { key: 'network', label: 'Network' },
    { key: 'incidents', label: 'Incidents' },
    { key: 'maintenance', label: 'Maintenance' },
  ];

  const softwareColumns: Column<InstalledSoftware>[] = [
    { key: 'name', header: 'Name', render: (s) => <span className="font-medium">{s.name}</span> },
    { key: 'version', header: 'Version', render: (s) => s.version || '—' },
    { key: 'publisher', header: 'Publisher', render: (s) => s.publisher || '—' },
    { key: 'install_date', header: 'Installed', render: (s) => s.install_date || '—' },
  ];

  const netColumns: Column<NetworkMetric>[] = [
    { key: 'interface_name', header: 'Interface', render: (n) => n.interface_name || '—' },
    { key: 'ip_address', header: 'IP', render: (n) => n.ip_address || '—' },
    { key: 'is_up', header: 'Up?', render: (n) => (n.is_up ? '✅' : '❌') },
    { key: 'latency_ms', header: 'Latency', render: (n) => n.latency_ms !== null ? `${n.latency_ms} ms` : '—' },
    { key: 'packet_loss_percent', header: 'Loss', render: (n) => n.packet_loss_percent !== null ? `${n.packet_loss_percent}%` : '—' },
    { key: 'recorded_at', header: 'Time', render: (n) => formatRelativeTime(n.recorded_at) },
  ];

  const incidentColumns: Column<Incident>[] = [
    { key: 'incident_number', header: 'Number' },
    { key: 'title', header: 'Title' },
    { key: 'severity', header: 'Severity', render: (i) => <SeverityBadge severity={i.severity} /> },
    { key: 'status', header: 'Status', render: (i) => titleCase(i.status) },
    { key: 'created_at', header: 'Reported', render: (i) => formatRelativeTime(i.created_at) },
  ];

  const maintColumns: Column<MaintenanceRecord>[] = [
    { key: 'title', header: 'Title' },
    { key: 'maintenance_type', header: 'Type', render: (m) => titleCase(m.maintenance_type) },
    { key: 'scheduled_date', header: 'Scheduled', render: (m) => m.scheduled_date || '—' },
    { key: 'completed_date', header: 'Completed', render: (m) => m.completed_date || '—' },
  ];

  return (
    <div className="space-y-4">
      <Button variant="ghost" onClick={() => navigate('/computers')} className="mb-2">
        <ArrowLeft className="h-4 w-4" /> Back
      </Button>

      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
            {computer.hostname}
            <StatusBadge status={computer.status} />
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Last seen: {formatRelativeTime(computer.last_seen)} · Registered: {formatDate(computer.registered_at)}
          </p>
        </div>
        {isAdmin && (
          <Button variant="secondary" onClick={generateKey}>
            <Key className="h-4 w-4" /> Generate Agent Key
          </Button>
        )}
      </div>

      {agentKey && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
          <p className="text-sm font-medium text-yellow-800">Agent API Key (shown once):</p>
          <code className="block mt-2 bg-yellow-100 p-2 rounded text-xs break-all font-mono">{agentKey}</code>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200">
        <div className="flex border-b border-slate-200 overflow-x-auto">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-5 py-3 text-sm font-medium border-b-2 whitespace-nowrap ${
                tab === t.key ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="p-5">
          {tab === 'overview' && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <SpecCard label="Processor" value={computer.processor} icon={<Cpu className="h-5 w-5 text-blue-600" />} />
              <SpecCard label="RAM" value={computer.ram_gb ? `${computer.ram_gb} GB` : null} icon={<MemoryStick className="h-5 w-5 text-purple-600" />} />
              <SpecCard label="Storage" value={computer.storage_gb ? `${computer.storage_gb} GB` : null} icon={<HardDrive className="h-5 w-5 text-green-600" />} />
              <SpecCard label="Operating System" value={`${computer.operating_system || '—'} ${computer.os_version || ''}`} />
              <SpecCard label="Manufacturer" value={computer.manufacturer} />
              <SpecCard label="Model" value={computer.model} />
              <SpecCard label="IP Address" value={computer.ip_address} />
              <SpecCard label="MAC Address" value={computer.mac_address} />
              <SpecCard label="Location" value={locationName} />
              <SpecCard label="Department" value={computer.department} />
          <SpecCard label="Uptime" value={latestHw ? formatUptime(latestHw.uptime_seconds) : null} icon={<Clock className="h-5 w-5 text-orange-600" />} />
              <SpecCard label="Last Seen" value={formatDateTime(computer.last_seen)} />
            </div>
          )}

          {tab === 'hardware' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard label="CPU" value={latestHw?.cpu_percent} unit="%" colour="text-blue-600" />
                <MetricCard label="RAM" value={latestHw?.ram_percent} unit="%" colour="text-purple-600" />
                <MetricCard label="Disk" value={latestHw?.disk_percent} unit="%" colour="text-green-600" />
                <MetricCard label="CPU Temp" value={latestHw?.cpu_temp_celsius} unit="°C" colour="text-orange-600" />
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <ChartCard title="CPU %" data={hwChart} dataKey="cpu" colour="#2563eb" />
                <ChartCard title="RAM %" data={hwChart} dataKey="ram" colour="#7c3aed" />
                <ChartCard title="Disk %" data={hwChart} dataKey="disk" colour="#16a34a" />
              </div>
            </div>
          )}

          {tab === 'software' && (
            <Table columns={softwareColumns} data={sw || []} rowKey={(s) => s.id}
              emptyMessage="No software inventory reported yet." />
          )}

          {tab === 'network' && (
            <div className="space-y-4">
              <Table columns={netColumns} data={netMetrics || []} rowKey={(n) => n.id}
                emptyMessage="No network metrics reported yet." />
            </div>
          )}

          {tab === 'incidents' && (
            <Table columns={incidentColumns} data={incidents || []} rowKey={(i) => i.id}
              emptyMessage="No incidents for this computer." />
          )}

          {tab === 'maintenance' && (
            <Table columns={maintColumns} data={maintenance || []} rowKey={(m) => m.id}
              emptyMessage="No maintenance records." />
          )}
        </div>
      </div>
    </div>
  );
}

function SpecCard({ label, value, icon }: { label: string; value: string | null; icon?: React.ReactNode }) {
  return (
    <div className="border border-slate-200 rounded-lg p-3">
      <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
        {icon} {label}
      </div>
      <div className="font-medium text-slate-800 truncate">{value || '—'}</div>
    </div>
  );
}

function MetricCard({ label, value, unit, colour }: { label: string; value: number | null | undefined; unit: string; colour: string }) {
  return (
    <div className="border border-slate-200 rounded-lg p-4 text-center">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`text-2xl font-bold ${colour}`}>
        {value === null || value === undefined ? 'N/A' : `${value.toFixed(1)}${unit}`}
      </div>
    </div>
  );
}

function ChartCard({ title, data, dataKey, colour }: { title: string; data: { time: string }[]; dataKey: string; colour: string }) {
  return (
    <div className="border border-slate-200 rounded-lg p-3">
      <div className="text-sm font-medium text-slate-700 mb-2">{title}</div>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" tick={{ fontSize: 10 }} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
          <Tooltip />
          <Line type="monotone" dataKey={dataKey} stroke={colour} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
