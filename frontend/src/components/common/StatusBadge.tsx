import Badge from './Badge';
import type { ComputerStatus } from '../../types';

const map: Record<ComputerStatus, { variant: 'green' | 'red' | 'yellow' | 'orange' | 'blue' | 'gray'; label: string }> = {
  online: { variant: 'green', label: 'Online' },
  offline: { variant: 'red', label: 'Offline' },
  warning: { variant: 'yellow', label: 'Warning' },
  critical: { variant: 'orange', label: 'Critical' },
  maintenance: { variant: 'blue', label: 'Maintenance' },
  unknown: { variant: 'gray', label: 'Unknown' },
};

export default function StatusBadge({ status }: { status: ComputerStatus }) {
  const cfg = map[status] || map.unknown;
  return <Badge variant={cfg.variant}>{cfg.label}</Badge>;
}
