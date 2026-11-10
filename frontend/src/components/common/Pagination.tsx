import Button from './Button';

interface PaginationProps {
  page: number;
  pages: number;
  total: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ page, pages, total, onPageChange }: PaginationProps) {
  if (pages <= 1) {
    return <div className="text-sm text-slate-500 py-2">Total: {total}</div>;
  }

  const pageButtons: number[] = [];
  const start = Math.max(1, page - 2);
  const end = Math.min(pages, page + 2);
  for (let i = start; i <= end; i++) pageButtons.push(i);

  return (
    <div className="flex items-center justify-between py-3">
      <div className="text-sm text-slate-500">
        Page {page} of {pages} · Total: {total}
      </div>
      <div className="flex items-center gap-1">
        <Button size="sm" variant="secondary" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
          Previous
        </Button>
        {start > 1 && (
          <>
            <Button size="sm" variant="ghost" onClick={() => onPageChange(1)}>1</Button>
            {start > 2 && <span className="px-1 text-slate-400">…</span>}
          </>
        )}
        {pageButtons.map((p) => (
          <Button
            key={p}
            size="sm"
            variant={p === page ? 'primary' : 'ghost'}
            onClick={() => onPageChange(p)}
          >
            {p}
          </Button>
        ))}
        {end < pages && (
          <>
            {end < pages - 1 && <span className="px-1 text-slate-400">…</span>}
            <Button size="sm" variant="ghost" onClick={() => onPageChange(pages)}>{pages}</Button>
          </>
        )}
        <Button size="sm" variant="secondary" disabled={page >= pages} onClick={() => onPageChange(page + 1)}>
          Next
        </Button>
      </div>
    </div>
  );
}
