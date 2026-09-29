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
    <div className="space-y-3">
      <p className="rounded-lg bg-amber-50 px-4 py-3 text-xs text-amber-800 ring-1 ring-inset ring-amber-200">
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
        className="w-full rounded-lg border border-slate-300 p-3 font-mono text-xs disabled:bg-slate-100"
      />
      {localError && <p className="text-sm text-red-600">{localError}</p>}
      {!readOnly && <Button onClick={save} loading={busy}>Save test page (JSON)</Button>}
    </div>
  );
}