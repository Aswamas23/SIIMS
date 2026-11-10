import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import settingsService from '../services/settings.service';
import Button from '../components/common/Button';
import { useAuth } from '../hooks/useAuth';

type Tab = 'general' | 'thresholds' | 'email' | 'notifications' | 'retention';

export default function SettingsPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>('general');

  if (user?.role !== 'system_admin') {
    return <div className="py-20 text-center text-slate-500">You do not have permission to view this page.</div>;
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: 'general', label: 'General' },
    { key: 'thresholds', label: 'Thresholds' },
    { key: 'email', label: 'Email' },
    { key: 'notifications', label: 'Notifications' },
    { key: 'retention', label: 'Data Retention' },
  ];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">Settings</h1>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200">
        <div className="flex border-b border-slate-200 overflow-x-auto">
          {tabs.map((t) => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`px-5 py-3 text-sm font-medium border-b-2 whitespace-nowrap ${tab === t.key ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
              {t.label}
            </button>
          ))}
        </div>
        <div className="p-6">
          {tab === 'general' && <GeneralSettings />}
          {tab === 'thresholds' && <ThresholdSettings />}
          {tab === 'email' && <EmailSettings />}
          {tab === 'notifications' && <NotifSettings />}
          {tab === 'retention' && <RetentionSettings />}
        </div>
      </div>
    </div>
  );
}

type SettingPair = { key: string; value: string };

function useSaveSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (settings: SettingPair[]) => settingsService.updateSettings(settings),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['settings'] }),
  });
}

function useSettingMap() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: settingsService.getSettings,
    select: (data) => Object.fromEntries(data.map((s) => [s.key, s.value || ''])),
  });
}

function GeneralSettings() {
  const { data: map, isLoading } = useSettingMap();
  const save = useSaveSettings();
  const [form, setForm] = useState({ system_name: '', school_name: '', timezone: 'UTC' });
  const [loaded, setLoaded] = useState(false);

  if (map && !loaded) {
    setLoaded(true);
    setForm({
      system_name: map.system_name || 'SIIMS',
      school_name: map.school_name || '',
      timezone: map.timezone || 'UTC',
    });
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await save.mutateAsync(Object.entries(form).map(([key, value]) => ({ key, value })));
  };

  if (isLoading) return <div className="text-sm text-slate-500">Loading…</div>;

  return (
    <form onSubmit={submit} className="space-y-4 max-w-md">
      <FormField label="System Name" value={form.system_name} onChange={(v) => setForm((f) => ({ ...f, system_name: v }))} />
      <FormField label="School Name" value={form.school_name} onChange={(v) => setForm((f) => ({ ...f, school_name: v }))} />
      <FormField label="Timezone" value={form.timezone} onChange={(v) => setForm((f) => ({ ...f, timezone: v }))} placeholder="e.g. Africa/Johannesburg" />
      <Button type="submit" loading={save.isPending}>Save General Settings</Button>
      {save.isSuccess && <p className="text-sm text-green-600">Saved successfully.</p>}
    </form>
  );
}

function ThresholdSettings() {
  const { data: map, isLoading } = useSettingMap();
  const save = useSaveSettings();
  const [form, setForm] = useState({
    cpu_warning_percent: '90', ram_warning_percent: '90',
    disk_warning_percent: '90', disk_critical_percent: '95',
    offline_timeout_minutes: '10', heartbeat_interval_seconds: '60',
    data_retention_days: '30',
  });
  const [loaded, setLoaded] = useState(false);

  if (map && !loaded) {
    setLoaded(true);
    setForm((f) => ({
      cpu_warning_percent: map.cpu_warning_percent || f.cpu_warning_percent,
      ram_warning_percent: map.ram_warning_percent || f.ram_warning_percent,
      disk_warning_percent: map.disk_warning_percent || f.disk_warning_percent,
      disk_critical_percent: map.disk_critical_percent || f.disk_critical_percent,
      offline_timeout_minutes: map.offline_timeout_minutes || f.offline_timeout_minutes,
      heartbeat_interval_seconds: map.heartbeat_interval_seconds || f.heartbeat_interval_seconds,
      data_retention_days: map.data_retention_days || f.data_retention_days,
    }));
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await save.mutateAsync(Object.entries(form).map(([key, value]) => ({ key, value })));
  };

  if (isLoading) return <div className="text-sm text-slate-500">Loading…</div>;

  return (
    <form onSubmit={submit} className="space-y-4 max-w-md">
      <FormField label="CPU Warning (%)" value={form.cpu_warning_percent} onChange={(v) => setForm((f) => ({ ...f, cpu_warning_percent: v }))} type="number" />
      <FormField label="RAM Warning (%)" value={form.ram_warning_percent} onChange={(v) => setForm((f) => ({ ...f, ram_warning_percent: v }))} type="number" />
      <FormField label="Disk Warning (%)" value={form.disk_warning_percent} onChange={(v) => setForm((f) => ({ ...f, disk_warning_percent: v }))} type="number" />
      <FormField label="Disk Critical (%)" value={form.disk_critical_percent} onChange={(v) => setForm((f) => ({ ...f, disk_critical_percent: v }))} type="number" />
      <FormField label="Offline Timeout (minutes)" value={form.offline_timeout_minutes} onChange={(v) => setForm((f) => ({ ...f, offline_timeout_minutes: v }))} type="number" />
      <FormField label="Heartbeat Interval (seconds)" value={form.heartbeat_interval_seconds} onChange={(v) => setForm((f) => ({ ...f, heartbeat_interval_seconds: v }))} type="number" />
      <Button type="submit" loading={save.isPending}>Save Thresholds</Button>
      {save.isSuccess && <p className="text-sm text-green-600">Saved successfully.</p>}
    </form>
  );
}

function EmailSettings() {
  const { data: map, isLoading } = useSettingMap();
  const save = useSaveSettings();
  const [form, setForm] = useState({
    smtp_host: '', smtp_port: '587', smtp_user: '', smtp_password: '',
    smtp_from: '', smtp_tls: 'true',
  });
  const [loaded, setLoaded] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testMsg, setTestMsg] = useState('');

  if (map && !loaded) {
    setLoaded(true);
    setForm((f) => ({
      smtp_host: map.smtp_host || f.smtp_host,
      smtp_port: map.smtp_port || f.smtp_port,
      smtp_user: map.smtp_user || f.smtp_user,
      smtp_password: f.smtp_password, // Don't pre-fill password
      smtp_from: map.smtp_from || f.smtp_from,
      smtp_tls: map.smtp_tls || f.smtp_tls,
    }));
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const pairs = Object.entries(form).filter(([, v]) => v !== '').map(([key, value]) => ({ key, value }));
    await save.mutateAsync(pairs);
  };

  const testEmail = async () => {
    setTesting(true);
    setTestMsg('');
    try {
      const res = await settingsService.testEmail();
      setTestMsg(res.message);
    } catch {
      setTestMsg('Failed to send test email. Check SMTP settings.');
    } finally {
      setTesting(false);
    }
  };

  if (isLoading) return <div className="text-sm text-slate-500">Loading…</div>;

  return (
    <form onSubmit={submit} className="space-y-4 max-w-md">
      <FormField label="SMTP Host" value={form.smtp_host} onChange={(v) => setForm((f) => ({ ...f, smtp_host: v }))} placeholder="smtp.yourschool.edu" />
      <FormField label="SMTP Port" value={form.smtp_port} type="number" onChange={(v) => setForm((f) => ({ ...f, smtp_port: v }))} />
      <FormField label="SMTP Username" value={form.smtp_user} onChange={(v) => setForm((f) => ({ ...f, smtp_user: v }))} />
      <FormField label="SMTP Password" value={form.smtp_password} type="password" onChange={(v) => setForm((f) => ({ ...f, smtp_password: v }))} placeholder="Leave blank to keep current" />
      <FormField label="From Address" value={form.smtp_from} onChange={(v) => setForm((f) => ({ ...f, smtp_from: v }))} placeholder="siims@yourschool.edu" />
      <label className="flex items-center gap-2 text-sm text-slate-700">
        <input type="checkbox" checked={form.smtp_tls === 'true'} onChange={(e) => setForm((f) => ({ ...f, smtp_tls: e.target.checked ? 'true' : 'false' }))} />
        Use TLS
      </label>
      <div className="flex gap-3">
        <Button type="submit" loading={save.isPending}>Save Email Settings</Button>
        <Button type="button" variant="secondary" onClick={testEmail} loading={testing}>Send Test Email</Button>
      </div>
      {testMsg && <p className="text-sm text-blue-600">{testMsg}</p>}
      {save.isSuccess && <p className="text-sm text-green-600">Saved successfully.</p>}
    </form>
  );
}

function NotifSettings() {
  const { data: map, isLoading } = useSettingMap();
  const save = useSaveSettings();
  const [form, setForm] = useState({
    notify_computer_offline: 'true', notify_licence_expiry: 'true',
    notify_critical_alert: 'true', notify_maintenance_due: 'true',
  });
  const [loaded, setLoaded] = useState(false);

  if (map && !loaded) {
    setLoaded(true);
    setForm((f) => ({
      notify_computer_offline: map.notify_computer_offline || f.notify_computer_offline,
      notify_licence_expiry: map.notify_licence_expiry || f.notify_licence_expiry,
      notify_critical_alert: map.notify_critical_alert || f.notify_critical_alert,
      notify_maintenance_due: map.notify_maintenance_due || f.notify_maintenance_due,
    }));
  }

  const toggle = (k: string) => setForm((f) => ({ ...f, [k]: f[k as keyof typeof f] === 'true' ? 'false' : 'true' }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await save.mutateAsync(Object.entries(form).map(([key, value]) => ({ key, value })));
  };

  if (isLoading) return <div className="text-sm text-slate-500">Loading…</div>;

  const items = [
    { key: 'notify_computer_offline', label: 'Computer goes offline' },
    { key: 'notify_licence_expiry', label: 'Licence approaching expiry' },
    { key: 'notify_critical_alert', label: 'Critical hardware alert' },
    { key: 'notify_maintenance_due', label: 'Maintenance due' },
  ];

  return (
    <form onSubmit={submit} className="space-y-4 max-w-md">
      <div className="space-y-2">
        {items.map((item) => (
          <label key={item.key} className="flex items-center gap-3 text-sm text-slate-700">
            <input type="checkbox" checked={form[item.key as keyof typeof form] === 'true'} onChange={() => toggle(item.key)} className="rounded" />
            {item.label}
          </label>
        ))}
      </div>
      <Button type="submit" loading={save.isPending}>Save Notification Settings</Button>
      {save.isSuccess && <p className="text-sm text-green-600">Saved successfully.</p>}
    </form>
  );
}

function RetentionSettings() {
  const { data: map, isLoading } = useSettingMap();
  const save = useSaveSettings();
  const [form, setForm] = useState({ data_retention_days: '30', audit_retention_days: '365' });
  const [loaded, setLoaded] = useState(false);

  if (map && !loaded) {
    setLoaded(true);
    setForm((f) => ({
      data_retention_days: map.data_retention_days || f.data_retention_days,
      audit_retention_days: map.audit_retention_days || f.audit_retention_days,
    }));
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await save.mutateAsync(Object.entries(form).map(([key, value]) => ({ key, value })));
  };

  if (isLoading) return <div className="text-sm text-slate-500">Loading…</div>;

  return (
    <form onSubmit={submit} className="space-y-4 max-w-md">
      <FormField label="Hardware/Network Metrics Retention (days)" value={form.data_retention_days} type="number" onChange={(v) => setForm((f) => ({ ...f, data_retention_days: v }))} />
      <FormField label="Audit Log Retention (days)" value={form.audit_retention_days} type="number" onChange={(v) => setForm((f) => ({ ...f, audit_retention_days: v }))} />
      <Button type="submit" loading={save.isPending}>Save Retention Settings</Button>
      {save.isSuccess && <p className="text-sm text-green-600">Saved successfully.</p>}
    </form>
  );
}

function FormField({
  label, value, onChange, type = 'text', placeholder,
}: { label: string; value: string; onChange: (v: string) => void; type?: string; placeholder?: string }) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
    </div>
  );
}
