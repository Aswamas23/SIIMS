import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Monitor, Cpu, Wifi, Package, Key, AlertTriangle,
  Wrench, FileText, Users, ClipboardList, Settings, ShieldCheck,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

interface NavItem {
  label: string;
  to: string;
  icon: typeof LayoutDashboard;
  adminOnly?: boolean;
}

const sections: { heading: string; items: NavItem[] }[] = [
  {
    heading: 'Overview',
    items: [{ label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard }],
  },
  {
    heading: 'Monitoring',
    items: [
      { label: 'Computers', to: '/computers', icon: Monitor },
      { label: 'Hardware', to: '/hardware', icon: Cpu },
      { label: 'Network', to: '/network', icon: Wifi },
    ],
  },
  {
    heading: 'Inventory',
    items: [
      { label: 'Software', to: '/software', icon: Package },
      { label: 'Licences', to: '/licences', icon: Key },
    ],
  },
  {
    heading: 'Operations',
    items: [
      { label: 'Incidents', to: '/incidents', icon: AlertTriangle },
      { label: 'Maintenance', to: '/maintenance', icon: Wrench },
      { label: 'Reports', to: '/reports', icon: FileText },
    ],
  },
  {
    heading: 'Administration',
    items: [
      { label: 'Users', to: '/users', icon: Users, adminOnly: true },
      { label: 'Audit Logs', to: '/audit', icon: ClipboardList, adminOnly: true },
      { label: 'Settings', to: '/settings', icon: Settings, adminOnly: true },
    ],
  },
];

export default function Sidebar() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'system_admin';

  return (
    <aside className="w-64 bg-slate-900 text-white h-screen flex flex-col fixed left-0 top-0">
      <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-800">
        <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center">
          <ShieldCheck className="h-5 w-5 text-white" />
        </div>
        <div>
          <div className="font-bold text-lg leading-tight">SIIMS</div>
          <div className="text-xs text-slate-400 leading-tight">ICT Monitor</div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto py-4">
        {sections.map((section) => {
          const visibleItems = section.items.filter((i) => !i.adminOnly || isAdmin);
          if (visibleItems.length === 0) return null;
          return (
            <div key={section.heading} className="mb-6">
              <div className="px-6 mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                {section.heading}
              </div>
              {visibleItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-6 py-2.5 text-sm transition-colors ${
                      isActive
                        ? 'bg-slate-700 text-white border-l-4 border-blue-500'
                        : 'text-slate-300 hover:bg-slate-800 border-l-4 border-transparent'
                    }`
                  }
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
