import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus } from 'lucide-react';
import incidentsService from '../services/incidents.service';
import computersService from '../services/computers.service';
import usersService from '../services/users.service';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import Table, { Column } from '../components/common/Table';
import SeverityBadge from '../components/common/SeverityBadge';
import Select from '../components/common/Select';
import EmptyState from '../components/common/EmptyState';
import { formatRelativeTime, titleCase } from '../utils/formatters';
import type {
  Incident, IncidentCreate, IncidentCategory, IncidentSeverity, IncidentStatus, UpdateType,
} from '../types';

export default function IncidentsPage() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [detail, setDetail] = useState<Incident | null>(null);

  const { data: incidents, isLoading } = useQuery({
    queryKey: ['incidents', { status: statusFilter || undefined, severity: severityFilter || undefined }],
    queryFn: () =>
      incidentsService.listIncidents({
        status: (statusFilter || undefined) as IncidentStatus | undefined,
        severity: (severityFilter || undefined) as IncidentSeverity | undefined,
        limit: 200,
      }),
  });

  const columns: Column<Incident>[] = [
    { key: 'incident_number', header: 'Number', render: (i) => <span className="font-mono text-xs">{i.incident_number}</span> },
    { key: 'title', header: 'Title', render: (i) => <span className="font-medium">{i.title}</span> },
    { key: 'category', header: 'Category', render: (i) => titleCase(i.category) },
    { key: 'severity', header: 'Severity', render: (i) => <SeverityBadge severity={i.severity} /> },
    { key: 'status', header: 'Status', render: (i) => titleCase(i.status) },
    { key: 'computer_id', header: 'Computer', render: (i) => (i.computer_id ? `PC #${i.computer_id}` : '—') },
    { key: 'created_at', header: 'Reported', render: (i) => formatRelativeTime(i.created_at) },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Incidents</h1>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" /> Report Incident
        </Button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 flex flex-wrap items-end gap-3">
        <Select
          label="Status"
          value={statusFilter}
          onChange={setStatusFilter}
          placeholder="All statuses"
          options={[
            { value: 'open', label: 'Open' },
            { value: 'in_progress', label: 'In Progress' },
            { value: 'resolved', label: 'Resolved' },
            { value: 'closed', label: 'Closed' },
          ]}
          className="w-44"
        />
        <Select
          label="Severity"
          value={severityFilter}
          onChange={setSeverityFilter}
          placeholder="All severities"
          options={[
            { value: 'low', label: 'Low' },
            { value: 'medium', label: 'Medium' },
            { value: 'high', label: 'High' },
            { value: 'critical', label: 'Critical' },
          ]}
          className="w-44"
        />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="py-10 text-center text-slate-500">Loading…</div>
        ) : (incidents?.length ?? 0) === 0 ? (
          <EmptyState title="No incidents found" description="Reported incidents will appear here." />
        ) : (
          <Table columns={columns} data={incidents || []} rowKey={(i) => i.id} onRowClick={setDetail} />
        )}
      </div>

      {showCreate && (
        <CreateIncidentModal
          onClose={() => setShowCreate(false)}
          onCreated={async (data) => {
            await incidentsService.createIncident(data);
            qc.invalidateQueries({ queryKey: ['incidents'] });
            setShowCreate(false);
          }}
        />
      )}

      {detail && (
        <IncidentDetailModal
          incident={detail}
          onClose={() => setDetail(null)}
          onChanged={() => {
            qc.invalidateQueries({ queryKey: ['incidents'] });
            setDetail(null);
          }}
        />
      )}
    </div>
  );
}

function CreateIncidentModal({ onClose, onCreated }: { onClose: () => void; onCreated: (data: IncidentCreate) => void }) {
  const { data: computers } = useQuery({ queryKey: ['computers', 'all'], queryFn: () => computersService.listComputers({ limit: 500 }) });
  const [form, setForm] = useState<IncidentCreate>({
    title: '', description: '', category: 'other', severity: 'medium', computer_id: undefined,
  });
  const [saving, setSaving] = useState(false);
  const set = (k: keyof IncidentCreate, v: unknown) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) return;
    setSaving(true);
    try { await onCreated(form); } finally { setSaving(false); }
  };

  return (
    <Modal isOpen onClose={onClose} title="Report Incident" size="lg"
      footer={<><Button variant="secondary" onClick={onClose}>Cancel</Button><Button type="submit" form="inc-form" loading={saving}>Create</Button></>}>
      <form id="inc-form" onSubmit={submit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Title *</label>
          <input required value={form.title} onChange={(e) => set('title', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
          <textarea value={form.description || ''} onChange={(e) => set('description', e.target.value)} rows={3}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Select
            label="Category"
            value={form.category}
            onChange={(v) => set('category', v)}
            options={[
              { value: 'hardware', label: 'Hardware' },
              { value: 'software', label: 'Software' },
              { value: 'network', label: 'Network' },
              { value: 'security', label: 'Security' },
              { value: 'performance', label: 'Performance' },
              { value: 'maintenance', label: 'Maintenance' },
              { value: 'other', label: 'Other' },
            ]}
          />
          <Select
            label="Severity"
            value={form.severity}
            onChange={(v) => set('severity', v)}
            options={[
              { value: 'low', label: 'Low' },
              { value: 'medium', label: 'Medium' },
              { value: 'high', label: 'High' },
              { value: 'critical', label: 'Critical' },
            ]}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Computer (optional)</label>
          <select value={form.computer_id ?? ''} onChange={(e) => set('computer_id', e.target.value ? Number(e.target.value) : undefined)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
            <option value="">—</option>
            {(computers?.items || []).map((c) => <option key={c.id} value={c.id}>{c.hostname}</option>)}
          </select>
        </div>
      </form>
    </Modal>
  );
}

function IncidentDetailModal({
  incident, onClose, onChanged,
}: {
  incident: Incident;
  onClose: () => void;
  onChanged: () => void;
}) {
  const { data: users } = useQuery({ queryKey: ['users', 'all'], queryFn: () => usersService.getUsers({ limit: 200 }) });
  const [note, setNote] = useState('');
  const [assignUser, setAssignUser] = useState('');
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    // Re-fetch and re-open; simplest is to invalidate + close (parent refetches).
    onChanged();
  };

  const addNote = async () => {
    if (!note.trim()) return;
    setBusy(true);
    try {
      await incidentsService.addIncidentUpdate(incident.id, note, 'comment' as UpdateType);
      setNote('');
      await refresh();
    } finally { setBusy(false); }
  };

  const assign = async () => {
    if (!assignUser) return;
    setBusy(true);
    try {
      await incidentsService.assignIncident(incident.id, Number(assignUser));
      setAssignUser('');
      await refresh();
    } finally { setBusy(false); }
  };

  const resolve = async () => {
    setBusy(true);
    try { await incidentsService.resolveIncident(incident.id, 'Resolved by technician.'); await refresh(); } finally { setBusy(false); }
  };

  const close = async () => {
    setBusy(true);
    try { await incidentsService.closeIncident(incident.id); await refresh(); } finally { setBusy(false); }
  };

  return (
    <Modal isOpen onClose={onClose} title={`${incident.incident_number} — ${incident.title}`} size="lg">
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2 items-center">
          <SeverityBadge severity={incident.severity} />
          <span className="text-sm text-slate-500">Status: {titleCase(incident.status)}</span>
          <span className="text-sm text-slate-500">· Category: {titleCase(incident.category)}</span>
        </div>

        {incident.description && <p className="text-sm text-slate-700 bg-slate-50 p-3 rounded-lg">{incident.description}</p>}

        {/* Timeline */}
        <div>
          <h4 className="font-semibold text-slate-800 mb-2">Timeline</h4>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {incident.updates.length === 0 ? (
              <p className="text-sm text-slate-400">No updates yet.</p>
            ) : (
              incident.updates.map((u) => (
                <div key={u.id} className="text-sm border-l-2 border-blue-200 pl-3 py-1">
                  <div className="text-xs text-slate-500">{formatRelativeTime(u.created_at)} · {titleCase(u.update_type)}</div>
                  <div className="text-slate-700">{u.message}</div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-3 border-t border-slate-200 pt-3">
          <div className="flex gap-2">
            <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Add an update note…"
              className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            <Button onClick={addNote} loading={busy}>Add Note</Button>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select value={assignUser} onChange={(e) => setAssignUser(e.target.value)}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white">
              <option value="">Assign to…</option>
              {(users?.items || []).map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
            </select>
            <Button variant="secondary" onClick={assign} disabled={!assignUser || busy}>Assign</Button>
            {incident.status !== 'resolved' && incident.status !== 'closed' && (
              <Button variant="secondary" onClick={resolve} disabled={busy}>Mark Resolved</Button>
            )}
            {incident.status === 'resolved' && (
              <Button onClick={close} disabled={busy}>Close Incident</Button>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
}
