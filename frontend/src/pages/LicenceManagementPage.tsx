import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Pencil, Trash2, Link2 } from 'lucide-react';
import licencesService from '../services/licences.service';
import computersService from '../services/computers.service';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import Table, { Column } from '../components/common/Table';
import Badge from '../components/common/Badge';
import ConfirmDialog from '../components/common/ConfirmDialog';
import EmptyState from '../components/common/EmptyState';
import { useAuth } from '../hooks/useAuth';
import { daysUntilExpiry, formatDate } from '../utils/formatters';
import type { SoftwareLicence, LicenceCreate, LicenceStatus } from '../types';

export default function LicenceManagementPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'system_admin';
  const qc = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [editTarget, setEditTarget] = useState<SoftwareLicence | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<SoftwareLicence | null>(null);
  const [assignTarget, setAssignTarget] = useState<SoftwareLicence | null>(null);

  const { data: licences, isLoading } = useQuery({
    queryKey: ['licences'],
    queryFn: () => licencesService.listLicences({ limit: 500 }),
  });

  const { data: expiring } = useQuery({
    queryKey: ['licences-expiring'],
    queryFn: () => licencesService.getExpiringLicences(30),
  });

  const { data: computers } = useQuery({
    queryKey: ['computers', 'all'],
    queryFn: () => computersService.listComputers({ limit: 500 }),
    enabled: !!assignTarget,
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => licencesService.deleteLicence(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['licences'] }),
  });

  const statusVariant = (s: LicenceStatus): 'green' | 'red' | 'yellow' | 'gray' | 'blue' => {
    switch (s) {
      case 'active': return 'green';
      case 'expired': return 'red';
      case 'expiring_soon': return 'yellow';
      case 'perpetual': return 'blue';
      default: return 'gray';
    }
  };

  const columns: Column<SoftwareLicence>[] = [
    { key: 'software_name', header: 'Software', render: (l) => <span className="font-medium">{l.software_name}</span> },
    { key: 'vendor', header: 'Vendor', render: (l) => l.vendor || '—' },
    { key: 'licence_type', header: 'Type', render: (l) => l.licence_type || '—' },
    { key: 'seats', header: 'Seats', render: (l) => l.seats ?? '—' },
    { key: 'assignments_count', header: 'Assigned', render: (l) => l.assignments_count ?? 0 },
    { key: 'expiry_date', header: 'Expiry', render: (l) => formatDate(l.expiry_date) },
    {
      key: 'days',
      header: 'Days Left',
      render: (l) => {
        const d = daysUntilExpiry(l.expiry_date);
        if (d === null) return <span className="text-slate-400">—</span>;
        if (d < 0) return <Badge variant="red">Expired</Badge>;
        if (d <= 7) return <Badge variant="red">{d}d</Badge>;
        if (d <= 30) return <Badge variant="yellow">{d}d</Badge>;
        return <Badge variant="green">{d}d</Badge>;
      },
    },
    { key: 'status', header: 'Status', render: (l) => <Badge variant={statusVariant(l.status)}>{l.status}</Badge> },
    {
      key: 'actions',
      header: 'Actions',
      render: (l) =>
        isAdmin ? (
          <div className="flex gap-1">
            <button onClick={(e) => { e.stopPropagation(); setAssignTarget(l); }} className="p-1.5 hover:bg-slate-100 rounded" title="Assign"><Link2 className="h-4 w-4 text-blue-600" /></button>
            <button onClick={(e) => { e.stopPropagation(); setEditTarget(l); }} className="p-1.5 hover:bg-slate-100 rounded" title="Edit"><Pencil className="h-4 w-4 text-slate-600" /></button>
            <button onClick={(e) => { e.stopPropagation(); setDeleteTarget(l); }} className="p-1.5 hover:bg-slate-100 rounded" title="Delete"><Trash2 className="h-4 w-4 text-red-600" /></button>
          </div>
        ) : (
          '—'
        ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Licence Management</h1>
        {isAdmin && (
          <Button onClick={() => setShowAdd(true)}>
            <Plus className="h-4 w-4" /> Add Licence
          </Button>
        )}
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SummaryCard label="Total Licences" value={licences?.length ?? 0} />
        <SummaryCard label="Active" value={licences?.filter((l) => l.status === 'active').length ?? 0} />
        <SummaryCard label="Expiring ≤30d" value={expiring?.length ?? 0} colour="text-yellow-600" />
        <SummaryCard label="Expired" value={licences?.filter((l) => l.status === 'expired').length ?? 0} colour="text-red-600" />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="py-10 text-center text-slate-500">Loading…</div>
        ) : (licences?.length ?? 0) === 0 ? (
          <EmptyState title="No licences registered" description="Add a software licence to start tracking expiry." />
        ) : (
          <Table columns={columns} data={licences || []} rowKey={(l) => l.id} />
        )}
      </div>

      {/* Add modal */}
      {showAdd && (
        <LicenceFormModal
          title="Add Licence"
          onClose={() => setShowAdd(false)}
          onSubmit={async (data) => { await licencesService.createLicence(data); qc.invalidateQueries({ queryKey: ['licences'] }); setShowAdd(false); }}
        />
      )}

      {/* Edit modal */}
      {editTarget && (
        <LicenceFormModal
          title="Edit Licence"
          initial={editTarget}
          onClose={() => setEditTarget(null)}
          onSubmit={async (data) => {
            await licencesService.updateLicence(editTarget.id, data);
            qc.invalidateQueries({ queryKey: ['licences'] });
            setEditTarget(null);
          }}
        />
      )}

      {/* Assign modal */}
      {assignTarget && (
        <AssignModal
          licence={assignTarget}
          computers={computers?.items || []}
          onClose={() => setAssignTarget(null)}
          onAssign={async (computerId) => {
            await licencesService.assignLicence(assignTarget.id, computerId);
            qc.invalidateQueries({ queryKey: ['licences'] });
          }}
        />
      )}

      {/* Delete confirm */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        title="Delete Licence"
        message={`Delete the licence for "${deleteTarget?.software_name}"? This deactivates the record.`}
        confirmLabel="Delete"
        danger
        onCancel={() => setDeleteTarget(null)}
        onConfirm={async () => {
          if (deleteTarget) await deleteMut.mutateAsync(deleteTarget.id);
          setDeleteTarget(null);
        }}
      />
    </div>
  );
}

function SummaryCard({ label, value, colour = 'text-slate-800' }: { label: string; value: number; colour?: string }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
      <div className="text-sm text-slate-500">{label}</div>
      <div className={`text-2xl font-bold ${colour}`}>{value}</div>
    </div>
  );
}

function LicenceFormModal({
  title, initial, onClose, onSubmit,
}: {
  title: string;
  initial?: SoftwareLicence;
  onClose: () => void;
  onSubmit: (data: LicenceCreate) => void;
}) {
  const [form, setForm] = useState<LicenceCreate>({
    software_name: initial?.software_name || '',
    version: initial?.version || '',
    licence_key: '',
    licence_type: initial?.licence_type || '',
    vendor: initial?.vendor || '',
    seats: initial?.seats ?? undefined,
    purchase_date: initial?.purchase_date || '',
    expiry_date: initial?.expiry_date || '',
    cost: initial?.cost ?? undefined,
    notes: initial?.notes || '',
  });
  const [saving, setSaving] = useState(false);

  const set = (k: keyof LicenceCreate, v: unknown) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.software_name.trim()) return;
    setSaving(true);
    try { await onSubmit(form); } finally { setSaving(false); }
  };

  return (
    <Modal isOpen onClose={onClose} title={title} size="lg"
      footer={<><Button variant="secondary" onClick={onClose}>Cancel</Button><Button type="submit" form="lic-form" loading={saving}>Save</Button></>}>
      <form id="lic-form" onSubmit={submit} className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <label className="block text-sm font-medium text-slate-700 mb-1">Software Name *</label>
          <input required value={form.software_name} onChange={(e) => set('software_name', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <FormField label="Version" value={form.version || ''} onChange={(v) => set('version', v)} />
        <FormField label="Vendor" value={form.vendor || ''} onChange={(v) => set('vendor', v)} />
        <FormField label="Licence Type" value={form.licence_type || ''} onChange={(v) => set('licence_type', v)} />
        <FormField label="Seats" type="number" value={form.seats ?? ''} onChange={(v) => set('seats', v ? Number(v) : undefined)} />
        <FormField label="Purchase Date" type="date" value={form.purchase_date || ''} onChange={(v) => set('purchase_date', v)} />
        <FormField label="Expiry Date" type="date" value={form.expiry_date || ''} onChange={(v) => set('expiry_date', v)} />
        <FormField label="Cost (cents)" type="number" value={form.cost ?? ''} onChange={(v) => set('cost', v ? Number(v) : undefined)} />
        <div className="col-span-2">
          <label className="block text-sm font-medium text-slate-700 mb-1">Licence Key (optional, stored securely)</label>
          <input type="password" value={form.licence_key || ''} onChange={(e) => set('licence_key', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div className="col-span-2">
          <label className="block text-sm font-medium text-slate-700 mb-1">Notes</label>
          <textarea value={form.notes || ''} onChange={(e) => set('notes', e.target.value)} rows={2}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
      </form>
    </Modal>
  );
}

function FormField({ label, value, onChange, type = 'text' }: { label: string; value: string | number; onChange: (v: string) => void; type?: string }) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
    </div>
  );
}

function AssignModal({
  licence, computers, onClose, onAssign,
}: {
  licence: SoftwareLicence;
  computers: { id: number; hostname: string }[];
  onClose: () => void;
  onAssign: (computerId: number) => void;
}) {
  const [selected, setSelected] = useState('');
  return (
    <Modal isOpen onClose={onClose} title={`Assign ${licence.software_name}`} size="sm"
      footer={<><Button variant="secondary" onClick={onClose}>Cancel</Button><Button disabled={!selected} onClick={async () => { if (selected) { await onAssign(Number(selected)); onClose(); } }}>Assign</Button></>}>
      <p className="text-sm text-slate-600 mb-3">Select a computer to assign this licence to:</p>
      <select value={selected} onChange={(e) => setSelected(e.target.value)}
        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
        <option value="">— Select computer —</option>
        {computers.map((c) => <option key={c.id} value={c.id}>{c.hostname}</option>)}
      </select>
    </Modal>
  );
}
