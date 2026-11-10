import Badge from './Badge';
import type { IncidentSeverity, AlertSeverity } from '../../types';

type Severity = IncidentSeverity | AlertSeverity | string;

const map: Record<string, { variant: 'gray' | 'green' | 'blue' | 'orange' | 'red' | 'yellow'; label: string }> = {
  low: { variant: 'green', label: 'Low' },
  medium: { variant: 'blue', label: 'Medium' },
  high: { variant: 'orange', label: 'High' },
  critical: { variant: 'red', label: 'Critical' },
  warning: { variant: 'yellow', label: 'Warning' },
  info: { variant: 'blue', label: 'Info' },
};

export default function SeverityBadge({ severity }: { severity: Severity }) {
  const cfg = map[severity] || { variant: 'gray' as const, label: severity };
  return <Badge variant={cfg.variant}>{cfg.label}</Badge>;
}
