export function PassFailBadge({ pass }: { pass: boolean | null }) {
  if (pass === null) {
    return (
      <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500 ring-1 ring-inset ring-slate-300">
        —
      </span>
    );
  }
  return pass ? (
    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800 ring-1 ring-inset ring-emerald-300">
      ✓ Pass
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-800 ring-1 ring-inset ring-red-300">
      ✗ Fail
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
      className={`inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${
        map[verdict] ?? map.PENDING
      }`}
    >
      {verdict === 'NOT_APPLICABLE' ? 'N/A' : verdict.charAt(0) + verdict.slice(1).toLowerCase()}
    </span>
  );
}