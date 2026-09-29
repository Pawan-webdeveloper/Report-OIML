/**
 * Authenticated file downloads / tab opening.
 * Blob + object URL keeps the Authorization header (plain <a href> can't).
 */
import { client } from '../api/client';

function filenameFrom(disposition: string | undefined, fallback: string): string {
  if (!disposition) return fallback;
  const m = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition);
  return m ? decodeURIComponent(m[1]) : fallback;
}

export async function downloadAuthed(path: string, fallbackName: string): Promise<void> {
  const res = await client.get(path, { responseType: 'blob' });
  const name = filenameFrom(
    res.headers['content-disposition'] as string | undefined,
    fallbackName,
  );
  const url = URL.createObjectURL(res.data as Blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export async function openPrintableHtml(path: string): Promise<void> {
  const res = await client.get(path, { responseType: 'blob' });
  const url = URL.createObjectURL(
    new Blob([res.data as Blob], { type: 'text/html' }),
  );
  window.open(url, '_blank', 'noopener');
  setTimeout(() => URL.revokeObjectURL(url), 120_000);
}