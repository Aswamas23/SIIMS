import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Pencil, Trash2, KeyRound } from 'lucide-react';
import usersService from '../services/users.service';
import Button from '../components/common/Button';
import Modal from '../components/common/Modal';
import Badge from '../components/common/Badge';
import Table, { Column } from '../components/common/Table';
import ConfirmDialog from '../components/common/ConfirmDialog';
import EmptyState from '../components/common/EmptyState';
import Select from '../components/common/Select';
import { useAuth } from '../hooks/useAuth';
import { formatDateTime, titleCase } from '../utils/formatters';
import type { User, UserCreate, UserRole, ResetPasswordResponse } from '../types';

const roleVariant = (r: UserRole): 'purple' | 'blue' | 'gray' =>
  r === 'system_admin' ? 'purple' : r === 'ict_technician' ? 'blue' : 'gray';

export default function UserManagementPage() {
  const { user: current } = useAuth();
  const qc = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [editTarget, setEditTarget] = useState<User | null>(null);
  const [deactivateTarget, setDeactivateTarget] = useState<User | null>(null);
  const [resetTarget, setResetTarget] = useState<User | null>(null);
  const [resetResult, setResetResult] = useState<ResetPasswordResponse | null>(null);

  const { data: usersData, isLoading } = useQuery({
    queryKey: ['users', 'all'],
    queryFn: () => usersService.getUsers({ limit: 200 }),
    enabled: current?.role === 'system_admin',
  });

  const deactivateMut = useMutation({
    mutationFn: (id: number) => usersService.deactivateUser(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  });

  const resetMut = useMutation({
    mutationFn: (id: number) => usersService.resetPassword(id),
    onSuccess: (res) => setResetResult(res),
  });

  if (current?.role !== 'system_admin') {
    return <div className="py-20 text-center text-slate-500">You do not have permission to view this page.</div>;
  }

  const columns: Column<User>[] = [
    { key: 'full_name', header: 'Name', render: (u) => <span className="font-medium">{u.full_name}</span> },
    { key: 'email', header: 'Email' },
    { key: 'role', header: 'Role', render: (u) => <Badge variant={roleVariant(u.role)}>{titleCase(u.role)}</Badge> },
    { key: 'is_active', header: 'Status', render: (u) => (u.is_active ? <Badge variant="green">Active</Badge> : <Badge variant="red">Inactive</Badge>) },
    { key: 'last_login', header: 'Last Login', render: (u) => formatDateTime(u.last_login) },
    {
      key: 'actions',
      header: 'Actions',
      render: (u) => (
        <div className="flex gap-1">
          <button onClick={(e) => { e.stopPropagation(); setEditTarget(u); }} className="p-1.5 hover:bg-slate-100 rounded" title="Edit"><Pencil className="h-4 w-4 text-slate-600" /></button>
          <button onClick={(e) => { e.stopPropagation(); setResetTarget(u); }} className="p-1.5 hover:bg-slate-100 rounded" title="Reset Password"><KeyRound className="h-4 w-4 text-blue-600" /></button>
          {u.id !== current?.id && (
            <button onClick={(e) => { e.stopPropagation(); setDeactivateTarget(u); }} className="p-1.5 hover:bg-slate-100 rounded" title="Deactivate"><Trash2 className="h-4 w-4 text-red-600" /></button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">User Management</h1>
        <Button onClick={() => setShowAdd(true)}>
          <Plus className="h-4 w-4" /> Add User
        </Button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="py-10 text-center text-slate-500">Loading…</div>
        ) : (usersData?.items.length ?? 0) === 0 ? (
          <EmptyState title="No users found" />
        ) : (
          <Table columns={columns} data={usersData?.items || []} rowKey={(u) => u.id} />
        )}
      </div>

      {showAdd && (
        <UserFormModal
          title="Add User"
          onClose={() => setShowAdd(false)}
          onSubmit={async (data) => {
            await usersService.createUser(data);
            qc.invalidateQueries({ queryKey: ['users'] });
            setShowAdd(false);
          }}
        />
      )}

      {editTarget && (
        <UserFormModal
          title="Edit User"
          initial={editTarget}
          onClose={() => setEditTarget(null)}
          onSubmit={async (data) => {
            const { password, ...rest } = data;
            void password;
            await usersService.updateUser(editTarget.id, rest);
            qc.invalidateQueries({ queryKey: ['users'] });
            setEditTarget(null);
          }}
        />
      )}

      <ConfirmDialog
        isOpen={!!deactivateTarget}
        title="Deactivate User"
        message={`Deactivate "${deactivateTarget?.full_name}"? They will lose access immediately.`}
        confirmLabel="Deactivate"
        danger
        onCancel={() => setDeactivateTarget(null)}
        onConfirm={async () => {
          if (deactivateTarget) await deactivateMut.mutateAsync(deactivateTarget.id);
          setDeactivateTarget(null);
        }}
      />

      {/* Reset password confirmation */}
      <ConfirmDialog
        isOpen={!!resetTarget && !resetResult}
        title="Reset Password"
        message={`Reset password for "${resetTarget?.full_name}"? A temporary password will be generated.`}
        confirmLabel="Reset"
        onCancel={() => setResetTarget(null)}
        onConfirm={async () => {
          if (resetTarget) await resetMut.mutateAsync(resetTarget.id);
        }}
      />

      {/* Reset result */}
      <Modal isOpen={!!resetResult} onClose={() => { setResetResult(null); setResetTarget(null); }} title="Temporary Password" size="sm"
        footer={<Button onClick={() => { setResetResult(null); setResetTarget(null); }}>Done</Button>}>
        {resetResult && (
          <div className="space-y-2">
            <p className="text-sm text-slate-600">{resetResult.message}</p>
            <code className="block bg-slate-100 p-3 rounded font-mono text-sm break-all select-all">{resetResult.temp_password}</code>
            <p className="text-xs text-slate-400">Share this securely. The user should change it after logging in.</p>
          </div>
        )}
      </Modal>
    </div>
  );
}

function UserFormModal({
  title, initial, onClose, onSubmit,
}: {
  title: string;
  initial?: User;
  onClose: () => void;
  onSubmit: (data: UserCreate) => void;
}) {
  const [form, setForm] = useState<UserCreate>({
    email: initial?.email || '',
    full_name: initial?.full_name || '',
    password: '',
    role: initial?.role || 'ict_technician',
    phone: initial?.phone || '',
  });
  const [saving, setSaving] = useState(false);
  const set = (k: keyof UserCreate, v: unknown) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.email.trim() || !form.full_name.trim()) return;
    if (!initial && form.password.length < 8) return;
    setSaving(true);
    try { await onSubmit(form); } finally { setSaving(false); }
  };

  return (
    <Modal isOpen onClose={onClose} title={title} size="md"
      footer={<><Button variant="secondary" onClick={onClose}>Cancel</Button><Button type="submit" form="user-form" loading={saving}>Save</Button></>}>
      <form id="user-form" onSubmit={submit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Full Name *</label>
          <input required value={form.full_name} onChange={(e) => set('full_name', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Email *</label>
          <input type="email" required value={form.email} onChange={(e) => set('email', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <Select label="Role" value={form.role} onChange={(v) => set('role', v as UserRole)}
          options={[
            { value: 'system_admin', label: 'System Administrator' },
            { value: 'ict_technician', label: 'ICT Technician' },
            { value: 'school_management', label: 'School Management' },
          ]}
        />
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Phone</label>
          <input value={form.phone || ''} onChange={(e) => set('phone', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            {initial ? 'New Password (leave blank to keep current)' : 'Password * (min 8 chars)'}
          </label>
          <input type="password" value={form.password} onChange={(e) => set('password', e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
      </form>
    </Modal>
  );
}
