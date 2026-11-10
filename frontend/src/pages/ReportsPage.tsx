import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText, FileSpreadsheet, FileDown, Monitor, Cpu, Wifi, Package, Key, AlertTriangle, Wrench, Clock } from 'lucide-react';
import reportsService from '../services/reports.service';
import locationsService from '../services/locations.service';
import Button from '../components/common/Button';
import Spinner from '../components/common/Spinner';
import DateRangePicker from '../components/common/DateRangePicker';
import Select from '../components/common/Select';
import type { ReportType, ReportFormat, ReportFilters } from '../types';

interface ReportCardDef {
  type: ReportType;
  title: string;
  description: string;
  icon: React.ReactNode;
  supportsLocation?: boolean;
}

const REPORTS: ReportCardDef[] = [
  { type: 'computers', title: 'Computer Inventory', description: 'All registered computers with specs and status.', icon: <Monitor className="h-6 w-6 text-blue-600" />, supportsLocation: true },
  { type: 'hardware', title: 'Hardware Health', description: 'Latest hardware metrics and threshold breaches.', icon: <Cpu className="h-6 w-6 text-purple-600" />, supportsLocation: true },
  { type: 'network', title: 'Network Availability', description: 'Network status and connectivity history.', icon: <Wifi className="h-6 w-6 text-cyan-600" /> },
  { type: 'software', title: 'Software Inventory', description: 'Installed software across all computers.', icon: <Package className="h-6 w-6 text-green-600" /> },
  { type: 'licences', title: 'Software Licences', description: 'Licence status and expiry summary.', icon: <Key className="h-6 w-6 text-amber-600" /> },
  { type: 'incidents', title: 'Incidents', description: 'All incidents with severity and resolution status.', icon: <AlertTriangle className="h-6 w-6 text-red-600" /> },
  { type: 'maintenance', title: 'Maintenance', description: 'Scheduled and completed maintenance records.', icon: <Wrench className="h-6 w-6 text-orange-600" /> },
  { type: 'downtime', title: 'Computer Downtime', description: 'Offline durations per computer.', icon: <Clock className="h-6 w-6 text-slate-600" /> },
];

export default function ReportsPage() {
  const { data: locations } = useQuery({ queryKey: ['locations'], queryFn: locationsService.listLocations });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">Reports</h1>
      <p className="text-sm text-slate-500">Generate and download reports in PDF, Excel, or CSV format.</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {REPORTS.map((r) => (
          <ReportCard key={r.type} def={r} locations={locations || []} />
        ))}
      </div>
    </div>
  );
}

function ReportCard({ def, locations }: { def: ReportCardDef; locations: { id: number; name: string }[] }) {
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [locationId, setLocationId] = useState('');
  const [downloading, setDownloading] = useState<ReportFormat | null>(null);
  const [error, setError] = useState('');

  const download = async (format: ReportFormat) => {
    setDownloading(format);
    setError('');
    try {
      const filters: ReportFilters = {};
      if (from) filters.date_from = from;
      if (to) filters.date_to = to;
      if (locationId && def.supportsLocation) filters.location_id = Number(locationId);
      await reportsService.downloadReport(def.type, format, filters);
    } catch {
      setError('Download failed. Ensure the backend is reachable.');
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <div className="flex items-start gap-3 mb-3">
        <div className="h-11 w-11 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">{def.icon}</div>
        <div>
          <h3 className="font-semibold text-slate-800">{def.title}</h3>
          <p className="text-xs text-slate-500">{def.description}</p>
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-3 mb-4">
        <DateRangePicker from={from} to={to} onFromChange={setFrom} onToChange={setTo} />
        {def.supportsLocation && (
          <Select
            label="Location"
            value={locationId}
            onChange={setLocationId}
            placeholder="All"
            options={locations.map((l) => ({ value: l.id, label: l.name }))}
            className="w-48"
          />
        )}
      </div>

      <div className="flex gap-2">
        <Button size="sm" variant="danger" onClick={() => download('pdf')} loading={downloading === 'pdf'}>
          {!downloading && <FileText className="h-4 w-4" />} PDF
        </Button>
        <Button size="sm" variant="secondary" onClick={() => download('excel')} loading={downloading === 'excel'}>
          {!downloading && <FileSpreadsheet className="h-4 w-4" />} Excel
        </Button>
        <Button size="sm" variant="ghost" onClick={() => download('csv')} loading={downloading === 'csv'}>
          {!downloading && <FileDown className="h-4 w-4" />} CSV
        </Button>
      </div>

      {downloading && <div className="mt-3 flex items-center gap-2 text-xs text-slate-500"><Spinner size="sm" /> Generating {downloading.toUpperCase()}…</div>}
      {error && <p className="mt-3 text-xs text-red-600">{error}</p>}
    </div>
  );
}
