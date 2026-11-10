import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Wrench } from 'lucide-react';
import maintenanceService from '../services/maintenance.service';
import computersService from '../services/computers.service';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import Table, { Column } from '../components/common/Table';
import Badge from '../components/common/Badge';
import Select from '../components/common/Select';
import EmptyState from '../components/common/EmptyState';
import { formatDate, titleCase } from '../utils/formatters';
import type { MaintenanceRecord, MaintenanceCreate, MaintenanceType } from '../types';

export default function MaintenancePage() {
  const qc = useQueryClient();
  const [view, setView] = useState<'table' | 'calendar'>('table');
  const [showSchedule, setShowSchedule] = useState(false);
  const [completeTarget, setCompleteTarget] = useState<MaintenanceRecord | null>(null);

  const { data: records, isLoading } = useQuery({
    queryKey: ['maintenance'],
    queryFn: () => maintenanceService.listMaintenance({ limit: 200 }),
  });

  const { data: computers } = useQuery({
    queryKey: ['computers', 'all'],
    queryFn: () => computersService.listComputers({ limit: 500 }),
  });

  const columns: Column<MaintenanceRecord>[] = [
    { key: 'title', header: 'Title', render: (m) => <span className="font-medium">{m.title}</span> },
    { key: 'computer_id', header: 'Computer', render: (m) => computers?.items.find((c) => c.id === m.computer_id)?.hostname || `PC #${m.computer_id}` },
    { key: 'maintenance_type', header: 'Type', render: (m) => titleCase(m.maintenance_type) },
    { key: 'scheduled_date', header: 'Scheduled', render: (m) => formatDate(m.scheduled_date) },
    {
      key: 'completed_date',
      header: 'Completed',
      render: (m) => m.completed_date ? <Badge variant="green">{formatDate(m.completed_date)}</Badge> : <Badge variant="yellow">Pending</Badge>,
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (m) =>
        !m.completed_date ? (
          <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); setCompleteTarget(m); }}>Mark Complete</Button>
        ) : (
          '—'
        ),
    },
  ];

  // Simple calendar: group by date string.
  const byDate = (records || []).reduce<Record<string, MaintenanceRecord[]>>((acc, m) => {
    if (m.scheduled_date) {
      (acc[m.scheduled_date] = acc[m.scheduled_date] || []).push(m);
    }
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Maintenance</h1>
        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-lg border border-slate-300 overflow-hidden">
            <button onClick={() => setView('table')} className={`px-3 py-1.5 text-sm ${view === 'table' ? 'bg-blue-600 text-white' : 'bg-white text-slate-600'}`}>Table</button>
            <button onClick={() => setView('calendar')} className={`px-3 py-1.5 text-sm ${view === 'calendar' ? 'bg-blue-600 text-white' : 'bg-white text-slate-600'}`}>Calendar</button>
          </div>
          <Button onClick={() => setShowSchedule(true)}>
            <Plus className="h-4 w-4" /> Schedule
          </Button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="py-10 text-center text-slate-500">Loading…</div>
        ) : view === 'table' ? (
          (records?.length ?? 0) === 0 ? (
            <EmptyState icon={<Wrench className="h-10 w-10" />} title="No maintenance records" description="Schedule preventive or corrective maintenance." />
          ) : (
            <Table columns={columns} data={records || []} rowKey={(m) => m.id} />
          )
        ) : (
          <div className="p-5">
            <div className="grid grid-cols-7 gap-1 text-center text-xs font-medium text-slate-500 mb-1">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => <div key={d} className="py-1">{d}</div>)}
            </div>
            <CalendarGrid recordsByDate={byDate} />
          </div>
        )}
      </div>

      {showSchedule && (
        <ScheduleModal
          computers={computers?.items || []}
          onClose={() => setShowSchedule(false)}
          onCreated={async (data) => {
            await maintenanceService.createMaintenance(data);
            qc.invalidateQueries({ queryKey: ['maintenance'] });
            setShowSchedule(false);
          }}
        />
      )}

      {completeTarget && (
        <CompleteModal
          record={completeTarget}
          onClose={() => setCompleteTarget(null)}
          onComplete={async (notes) => {
            await maintenanceService.completeMaintenance(completeTarget.id, { notes, completed_date: new Date().toISOString().slice(0, 10) });
            qc.invalidateQueries({ queryKey: ['maintenance'] });
            setCompleteTarget(null);
          }}
        />
      )}
    </div>
  );
}

function CalendarGrid({ recordsByDate }: { recordsByDate: Record<string, MaintenanceRecord[]> }) {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const first = new Date(year, month, 1);
  const startDay = first.getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const cells: (number | null)[] = [];
  for (let i = 0; i < startDay; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

  return (
    <div className="grid grid-cols-7 gap-1">
      {cells.map((d, i) => {
        if (d === null) return <div key={i} className="h-20 bg-slate-50 rounded" />;
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const items = recordsByDate[dateStr] || [];
        const isToday = d === now.getDate();
        return (
          <div key={i} className={`h-20 border border-slate-200 rounded p-1 overflow-hidden ${isToday ? 'bg-blue-50 border-blue-300' : ''}`}>
            <div className={`text-xs ${isToday ? 'font-bold text-blue-600' : 'text-slate-500'}`}>{d}</div>
            <div className="mt-1 space-y-0.5">
              {items.slice(0, 2).map((m) => (
                <div key={m.id} className="text-[10px] truncate px-1 py-0.5 bg-blue-100 text-blue-700 rounded">{m.title}</div>
              ))}
              {items.length > 2 && <div className="text-[10px] text-slate-400">+{items.length - 2} more</div>}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ScheduleModal({
  computers, onClose, onCreated,
}: {
  computers: { id: number; hostname: string }[];
  onClose: () => void;
  onCreated: (data: MaintenanceCreate) => void;
}) {
  const [form, setForm] = useState<MaintenanceCreate>({
    computer_id: 0, maintenance_type: 'preventive', title: '', description: '', scheduled_date: '', cost: undefined,
  });
  const [saving, setSaving] = useState(false);
  const set = (k: keyof MaintenanceCreate, v: unknown) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.computer_id || !form.title.trim()) return;
    setSaving(true);
    try { await onCreated(form); } finally { setSaving(false); }
  };

  return (
    <Modal isOpen onClose={onClose} title="Schedule Maintenance" size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Cancel</Button><Button type="submit" form="maint-form" loading={saving}>Schedule</Button></>}>
      <form id="maint-form" onSubmit={submit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Computer *</label>
          <select required value={form.computer_id || ''} onChange={(e) => set('computer_id', Number(e.target.value))}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">—</option>
            {computers.map((c) => <option key={c.id} value={c.id}>{c.hostname}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Title *</label>
          <input required value={form.title} onChange={(e) => set('title', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <Select label="Type" value={form.maintenance_type} onChange={(v) => set('maintenance_type', v as MaintenanceType)}
          options={[
            { value: 'preventive', label: 'Preventive' },
            { value: 'corrective', label: 'Corrective' },
            { value: 'upgrade', label: 'Upgrade' },
            { value: 'inspection', label: 'Inspection' },
            { value: 'other', label: 'Other' },
          ]}
        />
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Scheduled Date</label>
          <input type="date" value={form.scheduled_date || ''} onChange={(e) => set('scheduled_date', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
          <textarea value={form.description || ''} onChange={(e) => set('description', e.target.value)} rows={2}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
      </form>
    </Modal>
  );
}

function CompleteModal({
  record, onClose, onComplete,
}: {
  record: MaintenanceRecord;
  onClose: () => void;
  onComplete: (notes?: string) => void;
}) {
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  return (
    <Modal isOpen onClose={onClose} title="Complete Maintenance" size="sm"
      footer={<><Button variant="secondary" onClick={onClose}>Cancel</Button><Button loading={saving} onClick={async () => { setSaving(true); try { await onComplete(notes || undefined); } finally { setSaving(false); } }}>Mark Complete</Button></>}>
      <p className="text-sm text-slate-600 mb-3">Complete: <strong>{record.title}</strong></p>
      <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Completion notes (optional)…" rows={3}
        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
    </Modal>
  );
}
