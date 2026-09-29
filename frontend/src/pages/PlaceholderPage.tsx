import { Link, useParams } from 'react-router-dom';

export function PlaceholderPage({
  title,
  phase,
  description,
}: {
  title: string;
  phase: string;
  description: string;
}) {
  return (
    <div className="mx-auto mt-16 max-w-lg rounded-xl border border-slate-200 bg-white p-10 text-center shadow-sm">
      <p className="text-5xl">🚧</p>
      <h2 className="mt-4 text-lg font-semibold text-slate-800">{title}</h2>
      <p className="mt-2 text-sm text-slate-500">{description}</p>
      <p className="mt-4 inline-block rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700 ring-1 ring-inset ring-primary-200">
        Scheduled for {phase}
      </p>
    </div>
  );
}

export function EvaluationDetailPlaceholder() {
  const { id } = useParams();
  return (
    <PlaceholderPage
      title={`Evaluation detail — ${id?.slice(0, 8)}…`}
      phase="Phase 7"
      description="The page-by-page test entry workspace (weighing, eccentricity, repeatability…) with live pass/fail renders here."
    />
  );
}

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-100 p-6 text-center">
      <p className="text-6xl">🧭</p>
      <h1 className="mt-4 text-2xl font-bold text-slate-800">404 — Page not found</h1>
      <Link to="/" className="mt-4 text-sm font-medium text-primary-700 hover:underline">
        ← Back to Dashboard
      </Link>
    </div>
  );
}