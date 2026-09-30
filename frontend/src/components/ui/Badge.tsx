import type { EvalStatus, Outcome } from '../../types';
import { OUTCOME_STYLES, STATUS_STYLES, titleCase } from '../../lib/status';

export function Badge({ label, className = '' }: { label: string; className?: string }) {
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded px-2 py-1 text-[11px]
        font-semibold leading-none ring-1 ring-inset ${
          className || 'bg-slate-100 text-slate-700 ring-slate-300'
        }`}
    >
      {label}
    </span>
  );
}

export function StatusBadge({ status }: { status: EvalStatus }) {
  return <Badge label={titleCase(status)} className={STATUS_STYLES[status] ?? ''} />;
}

export function OutcomeBadge({ outcome }: { outcome: Outcome }) {
  return <Badge label={titleCase(outcome)} className={OUTCOME_STYLES[outcome] ?? ''} />;
}
