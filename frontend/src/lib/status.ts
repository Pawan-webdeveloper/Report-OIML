import type { EvalStatus, Outcome, Role } from '../types';

export function titleCase(value: string): string {
  return value
    .replaceAll('_', ' ')
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export const STATUS_STYLES: Record<EvalStatus, string> = {
  DRAFT: 'bg-slate-100 text-slate-700 ring-slate-300',
  IN_PROGRESS: 'bg-blue-50 text-blue-700 ring-blue-300',
  SUBMITTED: 'bg-amber-50 text-amber-700 ring-amber-300',
  UNDER_REVIEW: 'bg-amber-50 text-amber-700 ring-amber-300',
  RETURNED: 'bg-orange-50 text-orange-700 ring-orange-300',
  APPROVED: 'bg-emerald-50 text-emerald-700 ring-emerald-300',
  ARCHIVED: 'bg-slate-100 text-slate-500 ring-slate-300',
};

export const OUTCOME_STYLES: Record<Outcome, string> = {
  PASS: 'bg-emerald-100 text-emerald-800 ring-emerald-300',
  FAIL: 'bg-red-100 text-red-800 ring-red-300',
  INCOMPLETE: 'bg-slate-100 text-slate-600 ring-slate-300',
};

export const ROLE_STYLES: Record<Role, string> = {
  ADMIN: 'bg-purple-100 text-purple-800 ring-purple-300',
  ENGINEER: 'bg-blue-100 text-blue-800 ring-blue-300',
  REVIEWER: 'bg-amber-100 text-amber-800 ring-amber-300',
  VIEWER: 'bg-slate-100 text-slate-700 ring-slate-300',
};