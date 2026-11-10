interface ProgressBarProps {
  value: number | null | undefined;
  warningThreshold?: number;
  criticalThreshold?: number;
  label?: string;
}

/**
 * Coloured progress bar. Green below warning, yellow between warning and
 * critical, red at or above critical.
 */
export default function ProgressBar({
  value,
  warningThreshold = 90,
  criticalThreshold = 95,
  label,
}: ProgressBarProps) {
  const pct = value === null || value === undefined ? 0 : Math.min(100, Math.max(0, value));
  let colour = 'bg-green-500';
  if (value !== null && value !== undefined) {
    if (value >= criticalThreshold) colour = 'bg-red-500';
    else if (value >= warningThreshold) colour = 'bg-yellow-500';
  }
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
        <div className={`h-full ${colour} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-600 w-12 text-right">
        {value === null || value === undefined ? 'N/A' : `${value.toFixed(1)}%`}
      </span>
    </div>
  );
}
