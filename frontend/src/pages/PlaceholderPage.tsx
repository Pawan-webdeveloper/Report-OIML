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
    <section className="mx-auto mt-10 max-w-xl rounded-lg border border-slate-200 bg-white p-8 shadow-panel sm:p-10">
      <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.16em] text-primary-700">Module not yet active</p>
      <h2 className="mt-3 text-xl font-semibold tracking-tight text-slate-900">{title}</h2>
      <p className="mt-3 max-w-lg text-sm leading-6 text-slate-600">{description}</p>
      <p className="mt-6 inline-block rounded bg-primary-50 px-2.5 py-1 text-xs font-semibold text-primary-800 ring-1 ring-inset ring-primary-200">
        Scheduled for {phase}
      </p>
    </section>
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
    <main className="flex min-h-dvh items-center justify-center bg-slate-100 p-6">
      <div className="w-full max-w-lg border-l-4 border-primary-600 bg-white p-8 shadow-panel sm:p-10">
        <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-primary-700">Error 404</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">Page not found</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">The requested console page does not exist or is no longer available.</p>
        <Link to="/" className="mt-6 inline-flex rounded-md text-sm font-semibold text-primary-700 underline decoration-primary-300 underline-offset-4 hover:text-primary-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-600">
          Back to dashboard
        </Link>
      </div>
    </main>
  );
}
