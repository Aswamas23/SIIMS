import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Plus, Monitor } from 'lucide-react';
import { useComputers, useCreateComputer, useDeactivateComputer } from '../hooks/useComputers';
import locationsService from '../services/locations.service';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import StatusBadge from '../components/common/StatusBadge';
import Table, { Column } from '../components/common/Table';
import SearchInput from '../components/common/SearchInput';
import Select from '../components/common/Select';
import Pagination from '../components/common/Pagination';
import ConfirmDialog from '../components/common/ConfirmDialog';
import EmptyState from '../components/common/EmptyState';
import { useAuth } from '../hooks/useAuth';
import { formatRelativeTime } from '../utils/formatters';
import type { Computer, ComputerCreate, ComputerStatus } from '../types';

const PAGE_SIZE = 20;

export default function ComputersPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.role === 'system_admin';

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [locationFilter, setLocationFilter] = useState<string>('');
  const [showAdd, setShowAdd] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<Computer | null>(null);

  const { data, isLoading } = useComputers({
    skip: (page - 1) * PAGE_SIZE,
    limit: PAGE_SIZE,
    status: statusFilter ? (statusFilter as ComputerStatus) : undefined,
    location_id: locationFilter ? Number(locationFilter) : undefined,
    search: search || undefined,
  });

  const { data: locations } = useQuery({
    queryKey: ['locations'],
    queryFn: locationsService.listLocations,
  });

  const createMut = useCreateComputer();
  const deactivateMut = useDeactivateComputer();

  const columns: Column<Computer>[] = [
    { key: 'hostname', header: 'Hostname', render: (c) => <span className="font-medium text-blue-600">{c.hostname}</span> },
    { key: 'ip_address', header: 'IP Address', render: (c) => c.ip_address || '—' },
    { key: 'location_id', header: 'Location', render: (c) => locations?.find((l) => l.id === c.location_id)?.name || '—' },
    { key: 'operating_system', header: 'OS', render: (c) => c.operating_system || '—' },
    { key: 'status', header: 'Status', render: (c) => <StatusBadge status={c.status} /> },
    { key: 'last_seen', header: 'Last Seen', render: (c) => formatRelativeTime(c.last_seen) },
    {
      key: 'actions',
      header: 'Actions',
      render: (c) => (
        <div className="flex gap-1">
          <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); navigate(`/computers/${c.id}`); }}>
            View
          </Button>
          {isAdmin && (
            <Button
              size="sm"
              variant="ghost"
              onClick={(e) => { e.stopPropagation(); setConfirmDelete(c); }}
              className="text-red-600"
            >
              Deactivate
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Computers</h1>
        {isAdmin && (
          <Button onClick={() => setShowAdd(true)}>
            <Plus className="h-4 w-4" /> Add Computer
          </Button>
        )}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-48">
          <SearchInput value={search} onChange={setSearch} placeholder="Search hostname, IP, department…" />
        </div>
        <Select
          label="Status"
          value={statusFilter}
          onChange={setStatusFilter}
          placeholder="All statuses"
          options={[
            { value: 'online', label: 'Online' },
            { value: 'offline', label: 'Offline' },
            { value: 'warning', label: 'Warning' },
            { value: 'critical', label: 'Critical' },
            { value: 'maintenance', label: 'Maintenance' },
            { value: 'unknown', label: 'Unknown' },
          ]}
          className="w-40"
        />
        <Select
          label="Location"
          value={locationFilter}
          onChange={setLocationFilter}
          placeholder="All locations"
          options={(locations || []).map((l) => ({ value: l.id, label: l.name }))}
          className="w-48"
        />
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="py-10 text-center text-slate-500">Loading…</div>
        ) : (data?.items.length ?? 0) === 0 ? (
          <EmptyState icon={<Monitor className="h-10 w-10" />} title="No computers found" description="Register computers or adjust your filters." />
        ) : (
          <>
            <Table
              columns={columns}
              data={data?.items || []}
              onRowClick={(c) => navigate(`/computers/${c.id}`)}
              rowKey={(c) => c.id}
            />
            <div className="px-4">
              <Pagination
                page={page}
                pages={data?.pages || 1}
                total={data?.total || 0}
                onPageChange={setPage}
              />
            </div>
          </>
        )}
      </div>

      {/* Add computer modal */}
      {showAdd && (
        <AddComputerModal
          onClose={() => setShowAdd(false)}
          locations={locations || []}
          onSubmit={async (data) => {
            await createMut.mutateAsync(data);
            setShowAdd(false);
          }}
          loading={createMut.isPending}
        />
      )}

      {/* Deactivate confirm */}
      <ConfirmDialog
        isOpen={!!confirmDelete}
        title="Deactivate Computer"
        message={`Deactivate "${confirmDelete?.hostname}"? It will stop being monitored but its history is retained.`}
        confirmLabel="Deactivate"
        danger
        onCancel={() => setConfirmDelete(null)}
        onConfirm={async () => {
          if (confirmDelete) await deactivateMut.mutateAsync(confirmDelete.id);
          setConfirmDelete(null);
        }}
      />
    </div>
  );
}

// ---- Add Computer form modal ----
function AddComputerModal({
  onClose,
  onSubmit,
  locations,
  loading,
}: {
  onClose: () => void;
  onSubmit: (data: ComputerCreate) => void;
  locations: { id: number; name: string }[];
  loading: boolean;
}) {
  const [form, setForm] = useState<ComputerCreate>({
    hostname: '',
    ip_address: '', mac_address: '', manufacturer: '', model: '', processor: '',
    operating_system: '', os_version: '', department: '', location_id: undefined,
    ram_gb: undefined, storage_gb: undefined,
  });

  const set = (k: keyof ComputerCreate, v: unknown) => setForm((f) => ({ ...f, [k]: v }));

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.hostname.trim()) return;
    onSubmit(form);
  };

  return (
    <Modal isOpen onClose={onClose} title="Register Computer" size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" form="add-computer-form" loading={loading}>Save</Button>
        </>
      }
    >
      <form id="add-computer-form" onSubmit={submit} className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className="block text-sm font-medium text-slate-700 mb-1">Hostname *</label>
          <input required value={form.hostname} onChange={(e) => set('hostname', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <Field label="IP Address" value={form.ip_address || ''} onChange={(v) => set('ip_address', v)} />
        <Field label="MAC Address" value={form.mac_address || ''} onChange={(v) => set('mac_address', v)} />
        <Field label="Manufacturer" value={form.manufacturer || ''} onChange={(v) => set('manufacturer', v)} />
        <Field label="Model" value={form.model || ''} onChange={(v) => set('model', v)} />
        <Field label="Processor" value={form.processor || ''} onChange={(v) => set('processor', v)} />
        <Field label="OS" value={form.operating_system || ''} onChange={(v) => set('operating_system', v)} />
        <Field label="OS Version" value={form.os_version || ''} onChange={(v) => set('os_version', v)} />
        <Field label="RAM (GB)" type="number" value={form.ram_gb ?? ''} onChange={(v) => set('ram_gb', v ? Number(v) : undefined)} />
        <Field label="Storage (GB)" type="number" value={form.storage_gb ?? ''} onChange={(v) => set('storage_gb', v ? Number(v) : undefined)} />
        <Field label="Department" value={form.department || ''} onChange={(v) => set('department', v)} />
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Location</label>
          <select
            value={form.location_id ?? ''}
            onChange={(e) => set('location_id', e.target.value ? Number(e.target.value) : undefined)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          >
            <option value="">—</option>
            {locations.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
          </select>
        </div>
      </form>
    </Modal>
  );
}

function Field({ label, value, onChange, type = 'text' }: { label: string; value: string | number; onChange: (v: string) => void; type?: string }) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
    </div>
  );
}
