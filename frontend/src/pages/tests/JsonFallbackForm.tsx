import { useState } from 'react';
import { Button } from '../../components/ui/Button';
import type { TestFormProps } from './types';

/** Advanced entry for tests without a structured form yet (disturbances, temp, etc.). */
export default function JsonFallbackForm({ existing, readOnly, onSubmit }: TestFormProps) {
  const [text, setText] = useState(JSON.stringify(existing?.observations ?? {}, null, 2));
  const [localError, setLocalError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function save() {
    setLocalError(null);
    try {
      const parsed = JSON.parse(text) as Record<string, unknown>;
      setBusy(true);
      await onSubmit(parsed);
    } catch (e) {
      setLocalError(e instanceof SyntaxError ? `Invalid JSON: ${e.message}` : String(e));
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <p className="border-l-4 border-amber-500 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
        Advanced mode — raw observation JSON for this test page. The engine applies the same
        validation and pass/fail rules server-side. Structured forms for this test arrive in a
        later iteration.
      </p>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={readOnly}
        rows={14}
        spellCheck={false}
        aria-label="Raw observation JSON"
        className="w-full rounded-lg border border-slate-300 bg-slate-950 p-4 font-mono text-sm leading-6 text-slate-100 outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 disabled:bg-slate-100 disabled:text-slate-500"
      />
      {localError && <p role="alert" className="border-l-4 border-red-600 bg-red-50 px-4 py-3 text-sm text-red-800">{localError}</p>}
      {!readOnly && <Button className="min-h-12" onClick={save} loading={busy}>Save test page (JSON)</Button>}
    </div>
  );
}
