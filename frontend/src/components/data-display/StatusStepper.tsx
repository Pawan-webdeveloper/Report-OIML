import type { EvalStatus } from '../../types';

const STEPS: { key: EvalStatus; label: string }[] = [
  { key: 'DRAFT', label: 'Draft' },
  { key: 'IN_PROGRESS', label: 'In Progress' },
  { key: 'SUBMITTED', label: 'Submitted' },
  { key: 'UNDER_REVIEW', label: 'Review' },
  { key: 'APPROVED', label: 'Approved' },
];

export default function StatusStepper({ status }: { status: EvalStatus }) {
  const returned = status === 'RETURNED';
  const archived = status === 'ARCHIVED';
  const idx = returned ? 1 : STEPS.findIndex((s) => s.key === status);

  return (
    <ol aria-label="Evaluation status" className="flex flex-wrap items-center gap-y-2 text-xs">
      {STEPS.map((s, i) => {
        const done = i < idx || (archived && i === 4);
        const current = i === idx && !archived;
        const failed = returned && i === 1;
        return (
          <li key={s.key} className="flex items-center">
            {i > 0 && <span className={`mx-1 h-px w-3 ${done || current ? 'bg-primary-400' : 'bg-slate-300'}`} aria-hidden />}
            <span
              aria-current={current ? 'step' : undefined}
              className={`rounded px-2.5 py-1 font-semibold ring-1 ring-inset ${
                failed
                  ? 'bg-red-100 text-red-700 ring-red-300'
                  : current
                    ? 'bg-primary-600 text-white ring-primary-600'
                    : done
                      ? 'bg-emerald-50 text-emerald-700 ring-emerald-300'
                      : 'bg-white text-slate-400 ring-slate-200'
              }`}
            >
              {s.label}
              {failed && ' · Returned'}
            </span>
          </li>
        );
      })}
      {archived && (
        <span className="ml-2 rounded bg-slate-200 px-2.5 py-1 font-semibold text-slate-600">
          Archived
        </span>
      )}
    </ol>
  );
}
