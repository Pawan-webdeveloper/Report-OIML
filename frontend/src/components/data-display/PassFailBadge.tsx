export function PassFailBadge({ pass }: { pass: boolean | null }) {
  if (pass === null) {
    return (
      <span className="inline-flex items-center rounded bg-slate-100 px-2 py-1 text-[11px] font-semibold leading-none text-slate-500 ring-1 ring-inset ring-slate-300">
        —
      </span>
    );
  }
  return pass ? (
    <span className="inline-flex items-center gap-1.5 rounded bg-emerald-100 px-2 py-1 text-[11px] font-semibold leading-none text-emerald-900 ring-1 ring-inset ring-emerald-300">
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" aria-hidden /> Pass
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 rounded bg-red-100 px-2 py-1 text-[11px] font-semibold leading-none text-red-900 ring-1 ring-inset ring-red-300">
      <span className="h-1.5 w-1.5 rounded-full bg-red-600" aria-hidden /> Fail
    </span>
  );
}

export function VerdictBadge({ verdict }: { verdict: string | null | undefined }) {
  if (!verdict) return <span className="text-xs text-slate-400">Pending</span>;
  const map: Record<string, string> = {
    PASSED: 'bg-emerald-100 text-emerald-800 ring-emerald-300',
    FAILED: 'bg-red-100 text-red-800 ring-red-300',
    NOT_APPLICABLE: 'bg-slate-100 text-slate-600 ring-slate-300',
    PENDING: 'bg-slate-100 text-slate-500 ring-slate-300',
  };
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded px-2 py-1 text-[11px] font-semibold leading-none ring-1 ring-inset ${
        map[verdict] ?? map.PENDING
      }`}
    >
      {verdict === 'NOT_APPLICABLE' ? 'N/A' : verdict.charAt(0) + verdict.slice(1).toLowerCase()}
    </span>
  );
}
