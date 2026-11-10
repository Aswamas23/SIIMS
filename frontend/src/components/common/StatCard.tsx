import { ReactNode } from 'react';

interface StatCardProps {
  title: string;
  value: ReactNode;
  icon: ReactNode;
  color: 'blue' | 'green' | 'red' | 'yellow' | 'orange' | 'purple';
  subtitle?: string;
}

const colorMap = {
  blue: { bg: 'bg-blue-50', iconBg: 'bg-blue-600', text: 'text-blue-600' },
  green: { bg: 'bg-green-50', iconBg: 'bg-green-600', text: 'text-green-600' },
  red: { bg: 'bg-red-50', iconBg: 'bg-red-600', text: 'text-red-600' },
  yellow: { bg: 'bg-yellow-50', iconBg: 'bg-yellow-600', text: 'text-yellow-600' },
  orange: { bg: 'bg-orange-50', iconBg: 'bg-orange-600', text: 'text-orange-600' },
  purple: { bg: 'bg-purple-50', iconBg: 'bg-purple-600', text: 'text-purple-600' },
};

export default function StatCard({ title, value, icon, color, subtitle }: StatCardProps) {
  const c = colorMap[color];
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex items-center gap-4">
      <div className={`h-12 w-12 rounded-xl ${c.iconBg} flex items-center justify-center flex-shrink-0`}>
        {icon}
      </div>
      <div className="min-w-0">
        <div className="text-sm text-slate-500 truncate">{title}</div>
        <div className="text-2xl font-bold text-slate-800 leading-tight">{value}</div>
        {subtitle && <div className="text-xs text-slate-400 truncate">{subtitle}</div>}
      </div>
    </div>
  );
}
