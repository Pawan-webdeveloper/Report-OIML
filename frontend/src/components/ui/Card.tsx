export function Card({
  title,
  actions,
  children,
  className = '',
}: {
  title?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-lg border border-slate-200 bg-white shadow-panel ${className}`}>
      {(title || actions) && (
        <header className="flex min-h-12 items-center justify-between gap-4 border-b border-slate-200 px-5 py-3">
          <h2 className="text-sm font-semibold tracking-tight text-slate-900">{title}</h2>
          {actions}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}

export function KpiCard({
  label,
  value,
  tone = 'slate',
}: {
  label: string;
  value: number | string;
  tone?: 'slate' | 'blue' | 'amber' | 'emerald' | 'red';
}) {
  const tones: Record<string, string> = {
    slate: 'text-slate-900',
    blue: 'text-blue-800',
    amber: 'text-amber-800',
    emerald: 'text-emerald-800',
    red: 'text-red-800',
  };
  return (
    <div className="rounded-lg border border-slate-200 border-l-primary-600 bg-white p-5 shadow-panel [border-left-width:3px]">
      <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">{label}</p>
      <p className={`mt-2 font-mono text-3xl font-semibold tracking-tight ${tones[tone]}`}>{value}</p>
    </div>
  );
}
