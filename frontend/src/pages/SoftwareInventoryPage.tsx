import { useState, Fragment } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Package, ChevronDown, ChevronRight } from 'lucide-react';
import softwareService from '../services/software.service';
import computersService from '../services/computers.service';
import Table, { Column } from '../components/common/Table';
import SearchInput from '../components/common/SearchInput';
import Select from '../components/common/Select';
import Spinner from '../components/common/Spinner';
import EmptyState from '../components/common/EmptyState';
import { formatDate } from '../utils/formatters';
import type { InstalledSoftware, SoftwareSummaryItem } from '../types';

export default function SoftwareInventoryPage() {
  const [view, setView] = useState<'byComputer' | 'bySoftware'>('byComputer');
  const [search, setSearch] = useState('');
  const [computerId, setComputerId] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);

  // By Computer: list software for a selected computer.
  const { data: computers } = useQuery({
    queryKey: ['computers', 'all'],
    queryFn: () => computersService.listComputers({ limit: 500 }),
  });

  const { data: swData, isLoading } = useQuery({
    queryKey: ['software', { computerId, search }],
    queryFn: () =>
      softwareService.getSoftwareInventory({
        computer_id: computerId ? Number(computerId) : undefined,
        name: search || undefined,
        limit: 200,
      }),
    enabled: view === 'byComputer',
  });

  const { data: summary } = useQuery({
    queryKey: ['software-summary'],
    queryFn: softwareService.getSoftwareSummary,
    enabled: view === 'bySoftware',
  });

  const swColumns: Column<InstalledSoftware>[] = [
    { key: 'name', header: 'Name', render: (s) => <span className="font-medium">{s.name}</span> },
    { key: 'version', header: 'Version', render: (s) => s.version || '—' },
    { key: 'publisher', header: 'Publisher', render: (s) => s.publisher || '—' },
    { key: 'install_date', header: 'Install Date', render: (s) => formatDate(s.install_date) },
    { key: 'last_seen', header: 'Last Seen', render: (s) => formatDate(s.last_seen) },
  ];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">Software Inventory</h1>

      {/* View toggle */}
      <div className="inline-flex rounded-lg border border-slate-300 overflow-hidden">
        <button
          onClick={() => setView('byComputer')}
          className={`px-4 py-2 text-sm font-medium ${view === 'byComputer' ? 'bg-blue-600 text-white' : 'bg-white text-slate-600'}`}
        >
          By Computer
        </button>
        <button
          onClick={() => setView('bySoftware')}
          className={`px-4 py-2 text-sm font-medium ${view === 'bySoftware' ? 'bg-blue-600 text-white' : 'bg-white text-slate-600'}`}
        >
          By Software
        </button>
      </div>

      {view === 'byComputer' ? (
        <>
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 flex flex-wrap items-end gap-3">
            <Select
              label="Computer"
              value={computerId}
              onChange={setComputerId}
              placeholder="All computers"
              options={(computers?.items || []).map((c) => ({ value: c.id, label: c.hostname }))}
              className="w-64"
            />
            <div className="flex-1 min-w-48">
              <label className="block text-sm font-medium text-slate-700 mb-1">Search by name</label>
              <SearchInput value={search} onChange={setSearch} placeholder="Software name…" />
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            {isLoading ? (
              <div className="flex justify-center py-10"><Spinner /></div>
            ) : (swData?.items.length ?? 0) === 0 ? (
              <EmptyState icon={<Package className="h-10 w-10" />} title="No software found" />
            ) : (
              <Table columns={swColumns} data={swData?.items || []} rowKey={(s) => s.id} />
            )}
          </div>
        </>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          {summary && summary.length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="px-4 py-3 text-left font-semibold text-slate-600 w-8"></th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-600">Software</th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-600">Installations</th>
                  <th className="px-4 py-3 text-left font-semibold text-slate-600">Versions</th>
                </tr>
              </thead>
              <tbody>
                {summary.map((item: SoftwareSummaryItem) => (
                  <Fragment key={item.name}>
                    <tr
                      onClick={() => setExpanded(expanded === item.name ? null : item.name)}
                      className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer"
                    >
                      <td className="px-4 py-3">
                        {expanded === item.name ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      </td>
                      <td className="px-4 py-3 font-medium text-slate-800">{item.name}</td>
                      <td className="px-4 py-3">{item.count}</td>
                      <td className="px-4 py-3 text-slate-500">{item.versions.join(', ') || '—'}</td>
                    </tr>
                    {expanded === item.name && (
                      <tr className="bg-slate-50">
                        <td></td>
                        <td colSpan={3} className="px-4 py-3 text-slate-500 text-xs">
                          Installed across {item.count} computer(s). Known versions: {item.versions.join(', ') || 'unknown'}.
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          ) : (
            <EmptyState icon={<Package className="h-10 w-10" />} title="No software inventory" description="Software will appear here once agents report." />
          )}
        </div>
      )}
    </div>
  );
}
